"""
app.py - JARVIS v6 web interface backend with real persistence
"""

import json
from flask import jsonify, request
from jarvis_core import JARVISCore
from persistence import (
    TaskManager, MacroManager, NotificationManager,
    ChatHistoryManager, VaultManager
)

# ── Global core and managers ──
_core = None
_task_mgr = TaskManager()
_macro_mgr = MacroManager()
_notif_mgr = NotificationManager()
_chat_mgr = ChatHistoryManager()
_vault_mgr = VaultManager()

def set_core(core_instance):
    global _core
    _core = core_instance

def get_core():
    if _core is None:
        raise RuntimeError("JARVIS core not initialized")
    return _core

# ── Core endpoints ─────────────────────────────────────────────

def chat():
    data = request.get_json(force=True)
    message = data.get("message", "")
    conv_id = data.get("conversation_id")
    result = get_core().chat(message, tools_enabled=True)
    # Save to chat history
    if conv_id:
        # get existing chat
        chat_data = _chat_mgr.get(conv_id)
        if chat_data.get("ok") is not False:
            msgs = chat_data.get("messages", [])
        else:
            msgs = []
        msgs.append({"role": "user", "content": message})
        msgs.append({"role": "assistant", "content": result.get("response", "")})
        _chat_mgr.save(conv_id, msgs, title=message[:30])
    else:
        # new conversation
        conv_id = str(uuid.uuid4())
        msgs = [
            {"role": "user", "content": message},
            {"role": "assistant", "content": result.get("response", "")}
        ]
        _chat_mgr.save(conv_id, msgs, title=message[:30])
    return jsonify({
        "type": "final",
        "message": result.get("response", result.get("error", "No response")),
        "conversation_id": conv_id,
    })

def system_info():
    stats = get_core().get_stats()
    info = {
        "cpu_percent": stats.get("cpu", {}).get("usage_percent", 0),
        "memory_percent": stats.get("memory", {}).get("used_percent", 0),
        "disk_used_percent": stats.get("disk", {}).get("used_percent", 0),
    }
    return jsonify({"ok": True, "info": info})

def get_config():
    core = get_core()
    return jsonify(core.config)

def set_config():
    core = get_core()
    updates = request.get_json(force=True)
    result = core.update_config(updates)
    return jsonify(result)

# ── Tasks ──────────────────────────────────────────────────────

def tasks():
    if request.method == "GET":
        return jsonify({"tasks": _task_mgr.get_all()})
    elif request.method == "POST":
        data = request.get_json(force=True)
        task = _task_mgr.add(data.get("text", ""))
        return jsonify(task)
    return jsonify({"ok": False})

def task_detail(tid):
    if request.method == "POST":
        data = request.get_json(force=True)
        ok = _task_mgr.toggle(tid, data.get("done", False))
        return jsonify({"ok": ok})
    elif request.method == "DELETE":
        ok = _task_mgr.delete(tid)
        return jsonify({"ok": ok})
    return jsonify({"ok": False})

# ── Macros ─────────────────────────────────────────────────────

def macros():
    if request.method == "GET":
        return jsonify({"macros": _macro_mgr.get_all()})
    elif request.method == "POST":
        data = request.get_json(force=True)
        macro = _macro_mgr.add(data.get("name", ""), data.get("steps", []), data.get("description", ""))
        return jsonify(macro)
    return jsonify({"ok": False})

def macro_detail(name):
    if request.method == "DELETE":
        ok = _macro_mgr.delete(name)
        return jsonify({"ok": ok})
    return jsonify({"ok": False})

def macro_run(name):
    # Need to pass tool dispatch – we'll get from core's ALL_TOOL_SPECS and map
    core = get_core()
    # Build dispatch from core's tools (simplified)
    # Actually we'd need to map tool names to functions; for now, we'll just return a placeholder
    results = _macro_mgr.run(name, {})  # empty dispatch for now
    return jsonify({"ok": True, "step_results": results})

# ── Notifications ─────────────────────────────────────────────

def notifications():
    return jsonify({"notifications": _notif_mgr.get_all()})

def confirm():
    data = request.get_json(force=True)
    notif_id = data.get("id")  # Not used in current UI, but we'll implement
    approved = data.get("approved", False)
    # In current UI, they pass conversation_id, we need to find pending notification for that conv
    conv_id = data.get("conversation_id")
    notifs = _notif_mgr.get_all()
    for n in notifs:
        if n["conversation_id"] == conv_id and n["status"] == "pending":
            _notif_mgr.resolve(n["id"], approved)
            break
    return jsonify({"type": "final", "message": "Action approved" if approved else "Denied"})

# ── Chat History ─────────────────────────────────────────────

def chats():
    return jsonify({"chats": _chat_mgr.list_all()})

def chat_detail(cid):
    chat = _chat_mgr.get(cid)
    if chat.get("ok") is False:
        return jsonify({"ok": False, "error": "Not found"}), 404
    return jsonify({"ok": True, "chat": chat})

# ── Uploads / Files ──────────────────────────────────────────

def upload():
    # Simplified file upload – store in uploads folder
    upload_dir = Path(__file__).parent / "uploads"
    upload_dir.mkdir(exist_ok=True)
    files = []
    for f in request.files.getlist("files"):
        if f.filename:
            path = upload_dir / f.filename
            f.save(path)
            files.append({"name": f.filename, "size": path.stat().st_size})
    return jsonify({"ok": True, "files": files})

def uploads():
    upload_dir = Path(__file__).parent / "uploads"
    upload_dir.mkdir(exist_ok=True)
    files = []
    for f in upload_dir.iterdir():
        if f.is_file():
            files.append({
                "name": f.name,
                "size": f.stat().st_size,
                "category": "image" if f.suffix in [".jpg", ".png", ".gif"] else "file"
            })
    return jsonify({"files": files})

# ── Vaults ────────────────────────────────────────────────────

def vaults():
    if request.method == "GET":
        return jsonify({"vaults": _vault_mgr.list_vaults()})
    elif request.method == "POST":
        data = request.get_json(force=True)
        result = _vault_mgr.index_folder(data.get("folder_path", ""), data.get("vault_name", "default"))
        return jsonify(result)
    return jsonify({"ok": False})

def vault_detail(name):
    if request.method == "DELETE":
        ok = _vault_mgr.delete_vault(name)
        return jsonify({"ok": ok})
    return jsonify({"ok": False})

def vault_query(name):
    data = request.get_json(force=True)
    result = _vault_mgr.query(name, data.get("question", ""), data.get("top_k", 5))
    return jsonify(result)

def vault_all_query():
    # Query all vaults
    data = request.get_json(force=True)
    question = data.get("question", "")
    results = []
    for vault in _vault_mgr.list_vaults():
        res = _vault_mgr.query(vault["name"], question, data.get("top_k", 3))
        if res.get("ok") and res.get("results"):
            results.extend(res["results"])
    return jsonify({"ok": True, "results": results})

# ── Transcribe (voice) ──────────────────────────────────────

def transcribe():
    # Placeholder – you can implement with speech_recognition or Google Cloud
    return jsonify({"ok": False, "error": "Transcription not implemented"})

# ── Note: we also need to import uuid ──────────────────────
import uuid