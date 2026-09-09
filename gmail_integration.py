"""
gmail_integration.py - JARVIS Gmail Integration
Read, send, search, label emails via Gmail API (OAuth2)
100% FREE using Google Gmail API free tier
"""

import os
import json
import base64
import pickle
from pathlib import Path
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import List, Optional, Dict

try:
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from googleapiclient.discovery import build
    from googleapiclient.errors import HttpError
    GMAIL_OK = True
except ImportError:
    GMAIL_OK = False

GMAIL_DIR   = Path(__file__).parent / "gmail_data"
CREDS_FILE  = GMAIL_DIR / "credentials.json"
TOKEN_FILE  = GMAIL_DIR / "token.pickle"
GMAIL_DIR.mkdir(exist_ok=True)

SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/gmail.send",
    "https://www.googleapis.com/auth/gmail.modify",
    "https://www.googleapis.com/auth/gmail.labels",
]


class GmailClient:
    """Full Gmail integration via Google Gmail API"""

    def __init__(self):
        if not GMAIL_OK:
            raise ImportError(
                "Gmail API libraries not installed.\n"
                "Run: pip install google-auth google-auth-oauthlib "
                "google-auth-httplib2 google-api-python-client"
            )
        self.service = self._authenticate()

    # ── Auth ─────────────────────────────────────────────────

    def _authenticate(self):
        creds = None
        if TOKEN_FILE.exists():
            with open(TOKEN_FILE, "rb") as f:
                creds = pickle.load(f)

        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                if not CREDS_FILE.exists():
                    raise FileNotFoundError(
                        f"Gmail credentials.json not found at {CREDS_FILE}\n"
                        "Download from: https://console.cloud.google.com/apis/credentials\n"
                        "Create OAuth 2.0 Client ID → Desktop App → download JSON → "
                        f"save as {CREDS_FILE}"
                    )
                flow = InstalledAppFlow.from_client_secrets_file(
                    str(CREDS_FILE), SCOPES
                )
                creds = flow.run_local_server(port=0)

            with open(TOKEN_FILE, "wb") as f:
                pickle.dump(creds, f)

        return build("gmail", "v1", credentials=creds)

    # ── Read ─────────────────────────────────────────────────

    def list_emails(self, max_results: int = 10,
                    label: str = "INBOX", query: str = "") -> Dict:
        """List emails from Gmail."""
        try:
            q = f"label:{label} {query}".strip()
            result = self.service.users().messages().list(
                userId="me", maxResults=max_results, q=q
            ).execute()

            messages = result.get("messages", [])
            emails   = []
            for m in messages:
                msg = self.service.users().messages().get(
                    userId="me", id=m["id"], format="metadata",
                    metadataHeaders=["From", "To", "Subject", "Date"]
                ).execute()
                headers = {h["name"]: h["value"]
                           for h in msg["payload"].get("headers", [])}
                emails.append({
                    "id":      m["id"],
                    "from":    headers.get("From",    ""),
                    "to":      headers.get("To",      ""),
                    "subject": headers.get("Subject", "(no subject)"),
                    "date":    headers.get("Date",    ""),
                    "snippet": msg.get("snippet", ""),
                    "unread":  "UNREAD" in msg.get("labelIds", []),
                })
            return {"ok": True, "emails": emails, "count": len(emails)}
        except HttpError as e:
            return {"ok": False, "error": str(e)}

    def get_email(self, email_id: str) -> Dict:
        """Get full email content by ID."""
        try:
            msg = self.service.users().messages().get(
                userId="me", id=email_id, format="full"
            ).execute()

            headers = {h["name"]: h["value"]
                       for h in msg["payload"].get("headers", [])}
            body = self._extract_body(msg["payload"])

            return {
                "ok":      True,
                "id":      email_id,
                "from":    headers.get("From",    ""),
                "to":      headers.get("To",      ""),
                "subject": headers.get("Subject", "(no subject)"),
                "date":    headers.get("Date",    ""),
                "body":    body[:8000],
                "labels":  msg.get("labelIds", []),
            }
        except HttpError as e:
            return {"ok": False, "error": str(e)}

    def _extract_body(self, payload: dict) -> str:
        """Recursively extract plain-text body from payload."""
        if "parts" in payload:
            for part in payload["parts"]:
                if part.get("mimeType") == "text/plain":
                    data = part["body"].get("data", "")
                    if data:
                        return base64.urlsafe_b64decode(data).decode("utf-8", errors="replace")
            # Recurse into nested parts
            for part in payload["parts"]:
                result = self._extract_body(part)
                if result:
                    return result
        else:
            data = payload.get("body", {}).get("data", "")
            if data:
                return base64.urlsafe_b64decode(data).decode("utf-8", errors="replace")
        return ""

    def search_emails(self, query: str, max_results: int = 10) -> Dict:
        """Search emails using Gmail query syntax."""
        return self.list_emails(max_results=max_results, label="", query=query)

    def get_unread_count(self) -> Dict:
        """Get count of unread emails."""
        try:
            result = self.service.users().messages().list(
                userId="me", q="is:unread", maxResults=1
            ).execute()
            total = result.get("resultSizeEstimate", 0)
            return {"ok": True, "unread_count": total}
        except HttpError as e:
            return {"ok": False, "error": str(e)}

    # ── Send ─────────────────────────────────────────────────

    def send_email(self, to: str, subject: str, body: str,
                   html: bool = False, cc: str = "", bcc: str = "") -> Dict:
        """Send an email."""
        try:
            msg = MIMEMultipart("alternative")
            msg["To"]      = to
            msg["Subject"] = subject
            if cc:  msg["Cc"]  = cc
            if bcc: msg["Bcc"] = bcc

            mime_type = "html" if html else "plain"
            msg.attach(MIMEText(body, mime_type))

            raw = base64.urlsafe_b64encode(msg.as_bytes()).decode()
            self.service.users().messages().send(
                userId="me", body={"raw": raw}
            ).execute()

            return {"ok": True, "message": f"Email sent to {to}",
                    "subject": subject}
        except HttpError as e:
            return {"ok": False, "error": str(e)}

    def reply_email(self, email_id: str, body: str) -> Dict:
        """Reply to an email thread."""
        try:
            original = self.get_email(email_id)
            if not original["ok"]:
                return original

            msg = MIMEText(body)
            msg["To"]      = original["from"]
            msg["Subject"] = "Re: " + original["subject"]

            # Get thread ID
            thread_msg = self.service.users().messages().get(
                userId="me", id=email_id, format="minimal"
            ).execute()
            thread_id = thread_msg.get("threadId", email_id)

            raw = base64.urlsafe_b64encode(msg.as_bytes()).decode()
            self.service.users().messages().send(
                userId="me",
                body={"raw": raw, "threadId": thread_id}
            ).execute()

            return {"ok": True, "message": f"Reply sent to {original['from']}"}
        except HttpError as e:
            return {"ok": False, "error": str(e)}

    # ── Manage ───────────────────────────────────────────────

    def mark_as_read(self, email_id: str) -> Dict:
        """Mark email as read."""
        try:
            self.service.users().messages().modify(
                userId="me", id=email_id,
                body={"removeLabelIds": ["UNREAD"]}
            ).execute()
            return {"ok": True, "message": "Marked as read"}
        except HttpError as e:
            return {"ok": False, "error": str(e)}

    def mark_as_unread(self, email_id: str) -> Dict:
        """Mark email as unread."""
        try:
            self.service.users().messages().modify(
                userId="me", id=email_id,
                body={"addLabelIds": ["UNREAD"]}
            ).execute()
            return {"ok": True, "message": "Marked as unread"}
        except HttpError as e:
            return {"ok": False, "error": str(e)}

    def trash_email(self, email_id: str) -> Dict:
        """Move email to trash."""
        try:
            self.service.users().messages().trash(
                userId="me", id=email_id
            ).execute()
            return {"ok": True, "message": "Email moved to trash"}
        except HttpError as e:
            return {"ok": False, "error": str(e)}

    def add_label(self, email_id: str, label_name: str) -> Dict:
        """Add a label to an email (creates label if it doesn't exist)."""
        try:
            # Get or create label
            labels = self.service.users().labels().list(userId="me").execute()
            label_id = None
            for lbl in labels.get("labels", []):
                if lbl["name"].lower() == label_name.lower():
                    label_id = lbl["id"]
                    break

            if not label_id:
                new_lbl = self.service.users().labels().create(
                    userId="me", body={"name": label_name}
                ).execute()
                label_id = new_lbl["id"]

            self.service.users().messages().modify(
                userId="me", id=email_id,
                body={"addLabelIds": [label_id]}
            ).execute()
            return {"ok": True, "message": f"Label '{label_name}' added"}
        except HttpError as e:
            return {"ok": False, "error": str(e)}

    def list_labels(self) -> Dict:
        """List all Gmail labels."""
        try:
            result = self.service.users().labels().list(userId="me").execute()
            labels = [{"id": l["id"], "name": l["name"]}
                      for l in result.get("labels", [])]
            return {"ok": True, "labels": labels}
        except HttpError as e:
            return {"ok": False, "error": str(e)}

    def get_profile(self) -> Dict:
        """Get Gmail account profile."""
        try:
            profile = self.service.users().getProfile(userId="me").execute()
            return {
                "ok":           True,
                "email":        profile.get("emailAddress", ""),
                "total_msgs":   profile.get("messagesTotal", 0),
                "total_threads":profile.get("threadsTotal", 0),
            }
        except HttpError as e:
            return {"ok": False, "error": str(e)}


# ── Lazy singleton ────────────────────────────────────────────

_gmail_client: Optional[GmailClient] = None


def _get_gmail() -> tuple:
    global _gmail_client
    if _gmail_client is None:
        try:
            _gmail_client = GmailClient()
        except Exception as e:
            return None, str(e)
    return _gmail_client, None


# ── Tool functions ────────────────────────────────────────────

def gmail_list_emails(max_results: int = 10, label: str = "INBOX",
                      query: str = "") -> Dict:
    g, err = _get_gmail()
    if err: return {"ok": False, "error": err}
    return g.list_emails(max_results, label, query)


def gmail_get_email(email_id: str) -> Dict:
    g, err = _get_gmail()
    if err: return {"ok": False, "error": err}
    return g.get_email(email_id)


def gmail_search(query: str, max_results: int = 10) -> Dict:
    g, err = _get_gmail()
    if err: return {"ok": False, "error": err}
    return g.search_emails(query, max_results)


def gmail_send(to: str, subject: str, body: str,
               cc: str = "", bcc: str = "") -> Dict:
    g, err = _get_gmail()
    if err: return {"ok": False, "error": err}
    return g.send_email(to, subject, body, cc=cc, bcc=bcc)


def gmail_reply(email_id: str, body: str) -> Dict:
    g, err = _get_gmail()
    if err: return {"ok": False, "error": err}
    return g.reply_email(email_id, body)


def gmail_mark_read(email_id: str) -> Dict:
    g, err = _get_gmail()
    if err: return {"ok": False, "error": err}
    return g.mark_as_read(email_id)


def gmail_trash(email_id: str) -> Dict:
    g, err = _get_gmail()
    if err: return {"ok": False, "error": err}
    return g.trash_email(email_id)


def gmail_add_label(email_id: str, label_name: str) -> Dict:
    g, err = _get_gmail()
    if err: return {"ok": False, "error": err}
    return g.add_label(email_id, label_name)


def gmail_get_profile() -> Dict:
    g, err = _get_gmail()
    if err: return {"ok": False, "error": err}
    return g.get_profile()


def gmail_unread_count() -> Dict:
    g, err = _get_gmail()
    if err: return {"ok": False, "error": err}
    return g.get_unread_count()


# ── Tool schemas ──────────────────────────────────────────────

GMAIL_TOOL_SPECS = [
    {"type": "function", "function": {
        "name": "gmail_list_emails",
        "description": "List emails from Gmail inbox or any label.",
        "parameters": {"type": "object", "properties": {
            "max_results": {"type": "integer", "description": "Max emails to return (default 10)"},
            "label":       {"type": "string",  "description": "Gmail label (default INBOX)"},
            "query":       {"type": "string",  "description": "Gmail search query e.g. 'from:boss@co.com'"},
        }},
    }},
    {"type": "function", "function": {
        "name": "gmail_get_email",
        "description": "Get full email content by ID.",
        "parameters": {"type": "object", "properties": {
            "email_id": {"type": "string", "description": "Gmail message ID"},
        }, "required": ["email_id"]},
    }},
    {"type": "function", "function": {
        "name": "gmail_search",
        "description": "Search Gmail using query syntax (from:, subject:, is:unread, after:, etc.)",
        "parameters": {"type": "object", "properties": {
            "query":       {"type": "string",  "description": "Gmail search query"},
            "max_results": {"type": "integer", "description": "Max results"},
        }, "required": ["query"]},
    }},
    {"type": "function", "function": {
        "name": "gmail_send",
        "description": "RISKY: Send an email via Gmail.",
        "parameters": {"type": "object", "properties": {
            "to":      {"type": "string", "description": "Recipient email address"},
            "subject": {"type": "string", "description": "Email subject"},
            "body":    {"type": "string", "description": "Email body text"},
            "cc":      {"type": "string", "description": "CC addresses (optional)"},
            "bcc":     {"type": "string", "description": "BCC addresses (optional)"},
        }, "required": ["to", "subject", "body"]},
    }},
    {"type": "function", "function": {
        "name": "gmail_reply",
        "description": "RISKY: Reply to an email by ID.",
        "parameters": {"type": "object", "properties": {
            "email_id": {"type": "string", "description": "Email ID to reply to"},
            "body":     {"type": "string", "description": "Reply text"},
        }, "required": ["email_id", "body"]},
    }},
    {"type": "function", "function": {
        "name": "gmail_mark_read",
        "description": "Mark an email as read.",
        "parameters": {"type": "object", "properties": {
            "email_id": {"type": "string"},
        }, "required": ["email_id"]},
    }},
    {"type": "function", "function": {
        "name": "gmail_trash",
        "description": "RISKY: Move an email to trash.",
        "parameters": {"type": "object", "properties": {
            "email_id": {"type": "string"},
        }, "required": ["email_id"]},
    }},
    {"type": "function", "function": {
        "name": "gmail_add_label",
        "description": "Add a label to an email (creates label if needed).",
        "parameters": {"type": "object", "properties": {
            "email_id":   {"type": "string", "description": "Email ID"},
            "label_name": {"type": "string", "description": "Label name"},
        }, "required": ["email_id", "label_name"]},
    }},
    {"type": "function", "function": {
        "name": "gmail_get_profile",
        "description": "Get connected Gmail account info and message counts.",
        "parameters": {"type": "object", "properties": {}},
    }},
    {"type": "function", "function": {
        "name": "gmail_unread_count",
        "description": "Get number of unread emails in Gmail.",
        "parameters": {"type": "object", "properties": {}},
    }},
]

GMAIL_SAFE  = {
    "gmail_list_emails", "gmail_get_email", "gmail_search",
    "gmail_mark_read", "gmail_get_profile", "gmail_unread_count",
    "gmail_add_label",
}
GMAIL_RISKY = {"gmail_send", "gmail_reply", "gmail_trash"}

GMAIL_DISPATCH = {
    "gmail_list_emails":  gmail_list_emails,
    "gmail_get_email":    gmail_get_email,
    "gmail_search":       gmail_search,
    "gmail_send":         gmail_send,
    "gmail_reply":        gmail_reply,
    "gmail_mark_read":    gmail_mark_read,
    "gmail_trash":        gmail_trash,
    "gmail_add_label":    gmail_add_label,
    "gmail_get_profile":  gmail_get_profile,
    "gmail_unread_count": gmail_unread_count,
}
