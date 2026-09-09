"""
web_interface.py - JARVIS v6.1 Complete Web Interface
ALL TABS: Chat, Tasks, Files, Memory, Macros, Alerts, History, Core,
          Voice, Phone, System, Smart, Biometric, Gmail, Settings
Glassmorphic dark UI · WebSocket real-time · 100% FREE
"""

import json, os, time, uuid, threading, mimetypes, base64
from pathlib import Path
from datetime import datetime

from flask import Flask, jsonify, request, render_template_string
from flask_socketio import SocketIO, emit

# ─────────────────────────────────────────────────────────────
# HTML — single-file full UI
# ─────────────────────────────────────────────────────────────

HTML = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>J.A.R.V.I.S. v6</title>
<script src="https://cdn.socket.io/4.5.4/socket.io.min.js"></script>
<style>
:root{
  --bg:#020810;--glass:rgba(8,20,42,.55);--glass2:rgba(5,14,30,.7);
  --rim:rgba(63,216,232,.18);--accent:#3fd8e8;--accent2:#0ea5c8;
  --amber:#ffb347;--danger:#ff4d6d;--green:#39e07a;--purple:#b48efa;
  --text:#e2f0f8;--text2:#9ab8cc;--muted:#4a6a7e;--dim:#1e3244;
  --font:'IBM Plex Sans',system-ui,sans-serif;
  --mono:'IBM Plex Mono','Cascadia Code',monospace;
  --r:14px;--blur:blur(22px) saturate(170%);
}
*,*::before,*::after{box-sizing:border-box;margin:0;padding:0}
html,body{height:100%;overflow:hidden;background:var(--bg);color:var(--text);font-family:var(--font);-webkit-font-smoothing:antialiased}
body::before{content:'';position:fixed;inset:-60%;border-radius:50%;z-index:0;pointer-events:none;
  background:radial-gradient(ellipse 65% 50% at 20% 30%,rgba(63,216,232,.07) 0%,transparent 65%),
             radial-gradient(ellipse 55% 60% at 80% 70%,rgba(80,50,200,.06) 0%,transparent 60%);
  animation:aurora 28s ease-in-out infinite alternate}
@keyframes aurora{0%{transform:translate(0,0) scale(1)}100%{transform:translate(1%,-2%) scale(1.03)}}

.frame{position:relative;z-index:1;height:100vh;display:flex;flex-direction:column;padding:10px;gap:8px}

/* topbar */
.topbar{display:flex;align-items:center;justify-content:space-between;padding:10px 18px;
  background:var(--glass2);backdrop-filter:var(--blur);border:1px solid var(--rim);border-radius:var(--r);
  box-shadow:0 8px 32px rgba(0,0,0,.5),inset 0 1px 0 rgba(255,255,255,.05)}
.brand h1{font-size:14px;font-weight:700;letter-spacing:.06em;
  background:linear-gradient(100deg,var(--text) 40%,var(--accent));
  -webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text}
.brand small{font-family:var(--mono);font-size:9px;letter-spacing:.2em;color:var(--muted);text-transform:uppercase}
.status-chip{display:flex;align-items:center;gap:7px;font-family:var(--mono);font-size:11px;color:var(--text2);
  padding:5px 13px;background:rgba(255,255,255,.03);border:1px solid rgba(255,255,255,.06);border-radius:20px}
.led{width:7px;height:7px;border-radius:50%}
.led.on{background:var(--green);box-shadow:0 0 8px var(--green);animation:breathe 2s ease-in-out infinite}
.led.off{background:#1a2e3e}
@keyframes breathe{0%,100%{opacity:1}50%{opacity:.5}}

/* tabs */
.tabs{display:flex;gap:3px;padding:3px;background:rgba(3,10,24,.6);backdrop-filter:var(--blur);
  border:1px solid rgba(255,255,255,.06);border-radius:var(--r);overflow-x:auto;flex-wrap:nowrap}
.tabs::-webkit-scrollbar{height:3px}
.tabs::-webkit-scrollbar-thumb{background:rgba(63,216,232,.2);border-radius:3px}
.tab{background:transparent;border:1px solid transparent;color:var(--muted);
  padding:6px 10px;border-radius:10px;font-family:var(--font);font-size:11px;font-weight:600;
  cursor:pointer;white-space:nowrap;transition:.2s;flex:none}
.tab.active{background:rgba(63,216,232,.09);border-color:rgba(63,216,232,.22);color:var(--accent)}
.tab:hover:not(.active){color:var(--text2)}
.badge{display:inline-block;min-width:15px;padding:0 4px;background:var(--danger);
  border-radius:9px;font-size:10px;line-height:16px;text-align:center;margin-left:4px;vertical-align:middle}
.badge:empty{display:none}

/* main */
.main{flex:1;min-height:0;display:grid;grid-template-columns:1fr 255px;gap:8px}
.panel-col{min-height:0;display:flex;flex-direction:column;flex:1}
.panel{display:none;flex-direction:column;min-height:0;flex:1}
.panel.active{display:flex}

/* glass card */
.card{background:var(--glass);backdrop-filter:var(--blur);border:1px solid var(--rim);border-radius:var(--r);
  box-shadow:0 12px 48px rgba(0,0,0,.55),inset 0 1px 0 rgba(255,255,255,.04)}

/* scrollable panel */
.pscroll{flex:1;overflow-y:auto;background:var(--glass);backdrop-filter:var(--blur);
  border:1px solid var(--rim);border-radius:var(--r);padding:16px}
.pscroll::-webkit-scrollbar{width:3px}
.pscroll::-webkit-scrollbar-thumb{background:rgba(63,216,232,.15);border-radius:3px}

/* chat */
.chat-scroll{flex:1;overflow-y:auto;padding:16px;display:flex;flex-direction:column;gap:10px;scroll-behavior:smooth}
.chat-scroll::-webkit-scrollbar{width:3px}
.chat-scroll::-webkit-scrollbar-thumb{background:rgba(63,216,232,.18);border-radius:3px}
.msg{max-width:82%;padding:10px 14px;border-radius:12px;font-size:13.5px;line-height:1.65;white-space:pre-wrap;
  animation:msgpop .28s cubic-bezier(.16,1,.3,1) both}
@keyframes msgpop{from{opacity:0;transform:translateY(7px) scale(.97)}to{opacity:1;transform:none}}
.msg.user{align-self:flex-end;background:linear-gradient(145deg,rgba(25,70,105,.75),rgba(12,44,72,.8));
  border:1px solid rgba(63,216,232,.22);border-bottom-right-radius:4px}
.msg.assistant{align-self:flex-start;background:rgba(8,18,36,.7);
  border:1px solid rgba(255,255,255,.06);border-bottom-left-radius:4px}
.msg.system{align-self:center;max-width:94%;background:rgba(4,12,26,.5);
  border:1px dashed rgba(63,216,232,.12);font-family:var(--mono);font-size:11.5px;color:var(--muted);border-radius:10px}
.msg.error{align-self:flex-start;border:1px solid rgba(255,77,109,.3);background:rgba(255,77,109,.06)}
.msg.action-note{align-self:flex-start;border:1px solid rgba(255,255,255,.06);
  background:transparent;font-family:var(--mono);font-size:11px;color:var(--muted);padding:6px 11px;border-radius:8px}
.typing{display:flex;gap:4px;padding:4px 2px}
.typing span{width:6px;height:6px;border-radius:50%;background:var(--accent);opacity:.5;
  animation:bounce .9s ease-in-out infinite}
.typing span:nth-child(2){animation-delay:.15s}.typing span:nth-child(3){animation-delay:.3s}
@keyframes bounce{0%,60%,100%{transform:none;opacity:.5}30%{transform:translateY(-5px);opacity:1}}

/* composer */
.composer{padding:10px 12px;border-top:1px solid rgba(255,255,255,.06);background:rgba(3,10,22,.4)}
.composer-attachments{display:flex;flex-wrap:wrap;gap:6px;margin-bottom:8px}
.composer-attachments:empty{display:none}
.chip{display:flex;align-items:center;gap:6px;background:rgba(63,216,232,.07);
  border:1px solid rgba(63,216,232,.18);border-radius:20px;padding:3px 6px 3px 10px;
  font-family:var(--mono);font-size:11px}
.chip button{background:none;border:none;color:var(--muted);cursor:pointer;font-size:13px;line-height:1}
.chip button:hover{color:var(--danger)}
.composer-row{display:flex;gap:7px;align-items:flex-end}
textarea#inp{flex:1;resize:none;background:rgba(255,255,255,.04);border:1px solid rgba(255,255,255,.08);
  border-radius:10px;padding:9px 12px;color:var(--text);font-family:var(--font);font-size:13.5px;
  line-height:1.5;max-height:140px;overflow-y:auto;transition:.2s}
textarea#inp:focus{outline:none;border-color:rgba(63,216,232,.35);background:rgba(63,216,232,.04)}
textarea#inp::placeholder{color:var(--muted)}

/* buttons */
.btn{font-family:var(--font);font-weight:600;border-radius:10px;border:1px solid rgba(63,216,232,.45);
  background:linear-gradient(145deg,rgba(63,216,232,.88),rgba(20,140,165,.92));
  color:#020d14;padding:0 16px;height:36px;cursor:pointer;font-size:13px;
  transition:.15s;white-space:nowrap;flex:none}
.btn:hover{filter:brightness(1.12);transform:translateY(-1px)}
.btn:active{transform:none}
.btn:disabled{opacity:.35;cursor:default;transform:none}
.btn.ghost{background:rgba(255,255,255,.05);color:var(--text);border-color:rgba(255,255,255,.1)}
.btn.ghost:hover{background:rgba(255,255,255,.1)}
.btn.danger{background:linear-gradient(145deg,rgba(255,77,109,.9),rgba(180,30,55,.9));
  border-color:rgba(255,77,109,.4);color:#fff}
.btn.amber{background:linear-gradient(145deg,rgba(255,179,71,.9),rgba(180,110,20,.9));
  border-color:rgba(255,179,71,.4);color:#020d14}
.btn.sm{padding:0 11px;height:28px;font-size:11.5px}
.icon-btn{background:rgba(255,255,255,.05);border:1px solid rgba(255,255,255,.08);
  color:var(--text);width:36px;height:36px;border-radius:10px;cursor:pointer;
  font-size:14px;display:grid;place-items:center;transition:.15s;flex:none}
.icon-btn:hover{border-color:var(--rim);transform:translateY(-1px)}
.icon-btn.active{border-color:var(--danger);color:var(--danger);background:rgba(255,77,109,.12);
  animation:micring 1.2s ease-in-out infinite}
@keyframes micring{0%,100%{box-shadow:0 0 0 0 rgba(255,77,109,.4)}50%{box-shadow:0 0 0 6px rgba(255,77,109,0)}}

/* sidebar */
.sidebar{display:flex;flex-direction:column;gap:8px;min-height:0}
.sb-block{background:var(--glass2);backdrop-filter:var(--blur);border:1px solid var(--rim);
  border-radius:var(--r);padding:13px;display:flex;flex-direction:column;gap:6px}
.sb-block.grow{flex:1;min-height:0;overflow:hidden}
.eyebrow{font-family:var(--mono);font-size:9.5px;letter-spacing:.2em;text-transform:uppercase;color:var(--muted)}
.sys-row{display:flex;justify-content:space-between;font-family:var(--mono);font-size:11px;
  border-bottom:1px solid rgba(255,255,255,.04);padding-bottom:4px}
.sys-row span:first-child{color:var(--muted)}
.log-list{flex:1;overflow-y:auto;display:flex;flex-direction:column;gap:4px;font-family:var(--mono);font-size:10px}
.log-list::-webkit-scrollbar{width:2px}
.log-entry{color:var(--muted);border-left:2px solid rgba(255,255,255,.06);padding-left:6px;
  animation:fadein .2s ease both}
.log-entry.ok{border-color:var(--accent)}.log-entry.fail{border-color:var(--danger)}
.log-entry.warn{border-color:var(--amber)}
.log-t{opacity:.6;margin-right:4px}
@keyframes fadein{from{opacity:0;transform:translateY(5px)}to{opacity:1;transform:none}}

/* list cards */
.lcard{background:rgba(6,14,30,.6);border:1px solid rgba(255,255,255,.07);border-radius:11px;
  padding:10px 12px;transition:.2s;animation:fadein .3s both;margin-bottom:7px}
.lcard:hover{border-color:var(--rim);background:rgba(63,216,232,.04)}
.lcard:last-child{margin-bottom:0}
.hint{color:var(--muted);font-size:12px;line-height:1.6}

/* fields */
.field-label{font-family:var(--mono);font-size:9.5px;letter-spacing:.14em;text-transform:uppercase;
  color:var(--muted);margin:10px 0 4px}
.field-label:first-child{margin-top:0}
.inp{width:100%;background:rgba(255,255,255,.04);border:1px solid rgba(255,255,255,.08);
  border-radius:10px;padding:8px 11px;color:var(--text);font-family:var(--mono);font-size:12.5px;transition:.2s}
.inp:focus{outline:none;border-color:rgba(63,216,232,.35);background:rgba(63,216,232,.04)}
select.inp option{background:var(--bg)}

/* stats */
.stat-grid{display:grid;grid-template-columns:1fr 1fr;gap:8px;margin-bottom:12px}
.stat-tile{background:rgba(6,14,30,.6);border:1px solid rgba(255,255,255,.07);border-radius:11px;padding:11px}
.stat-tile .val{font-family:var(--mono);font-size:20px;color:var(--accent);font-weight:700;margin-top:4px}
.stat-tile .lbl{font-family:var(--mono);font-size:9px;letter-spacing:.15em;text-transform:uppercase;color:var(--muted)}
.pbar{background:rgba(255,255,255,.06);border-radius:99px;height:4px;margin-top:5px;overflow:hidden}
.pbar-fill{background:var(--accent);height:100%;border-radius:99px;transition:.5s}

/* toggles */
.toggle-row{display:flex;align-items:center;justify-content:space-between;
  padding:7px 0;border-bottom:1px solid rgba(255,255,255,.04)}
.toggle-row:last-child{border:none}
.toggle-row label:first-child{font-size:12.5px}
.toggle{position:relative;width:38px;height:21px}
.toggle input{opacity:0;width:0;height:0}
.tslider{position:absolute;inset:0;background:rgba(255,255,255,.1);border-radius:21px;cursor:pointer;transition:.25s}
.tslider::before{content:'';position:absolute;width:15px;height:15px;left:3px;top:3px;
  background:rgba(255,255,255,.4);border-radius:50%;transition:.25s}
.toggle input:checked+.tslider{background:var(--accent)}
.toggle input:checked+.tslider::before{transform:translateX(17px);background:#020d14}

/* task / vault / macro / notif cards */
.task-card{display:flex;align-items:center;gap:9px}
.task-card input[type=checkbox]{width:14px;height:14px;accent-color:var(--accent);flex:none}
.task-text{flex:1;font-size:13px}
.task-card.done .task-text{text-decoration:line-through;opacity:.5}

.notif-card{border-left:3px solid var(--amber);padding-left:10px}
.notif-card.approved{border-color:var(--accent);opacity:.65}
.notif-card.denied{opacity:.45}

/* vault badge */
.vbadge{display:inline-block;padding:2px 8px;border-radius:20px;font-family:var(--mono);font-size:9.5px;
  background:rgba(63,216,232,.09);color:var(--accent);border:1px solid rgba(63,216,232,.22)}
.vbadge.green{background:rgba(57,224,122,.09);color:var(--green);border-color:rgba(57,224,122,.28)}

/* emotion badge */
.ebadge{display:inline-block;padding:2px 8px;border-radius:20px;font-family:var(--mono);font-size:9.5px;margin-left:6px}
.emo-happy{background:rgba(57,224,122,.09);color:var(--green);border:1px solid rgba(57,224,122,.28)}
.emo-sad,.emo-anxious{background:rgba(255,179,71,.09);color:var(--amber);border:1px solid rgba(255,179,71,.28)}
.emo-angry{background:rgba(255,77,109,.09);color:var(--danger);border:1px solid rgba(255,77,109,.28)}
.emo-neutral{background:rgba(255,255,255,.04);color:var(--muted);border:1px solid rgba(255,255,255,.1)}

/* provider tabs (settings) */
.ptabs{display:flex;gap:4px;flex-wrap:wrap;margin-bottom:8px}
.ptab{background:rgba(255,255,255,.03);border:1px solid rgba(255,255,255,.08);color:var(--muted);
  padding:5px 11px;border-radius:8px;font-family:var(--mono);font-size:10.5px;cursor:pointer;transition:.18s}
.ptab.active{border-color:rgba(63,216,232,.32);color:var(--accent);background:rgba(63,216,232,.07)}
.ppane{display:none}.ppane.active{display:block;animation:fadein .2s both}

@media(max-width:860px){.main{grid-template-columns:1fr}.sidebar{display:none}}
</style>
</head>
<body>
<div class="frame">

<!-- TOPBAR -->
<header class="topbar">
  <div class="brand">
    <small>J.A.R.V.I.S. · LOCAL CONSOLE</small>
    <h1>Just A Really Virtuous Intelligent System &nbsp;·&nbsp; v6</h1>
  </div>
  <div style="display:flex;gap:8px;align-items:center">
    <div class="status-chip"><span class="led off" id="conn-led"></span><span id="conn-text">Connecting…</span></div>
    <button class="icon-btn" id="new-chat-btn" title="New chat">＋</button>
    <button class="icon-btn" id="mic-btn" title="Voice">🎤</button>
    <button class="icon-btn" onclick="switchTab('settings')" title="Settings">⚙</button>
  </div>
</header>

<!-- TABS (all 15) -->
<nav class="tabs" id="tabbar">
  <button class="tab active" data-tab="chat">💬 Chat</button>
  <button class="tab" data-tab="tasks">✅ Tasks</button>
  <button class="tab" data-tab="files">📁 Files</button>
  <button class="tab" data-tab="vault">🧠 Memory</button>
  <button class="tab" data-tab="macros">⚡ Macros</button>
  <button class="tab" data-tab="notifications">🔔 Alerts<span class="badge" id="notif-badge"></span></button>
  <button class="tab" data-tab="history">🗂 History</button>
  <button class="tab" data-tab="core">🌀 Core</button>
  <button class="tab" data-tab="voice">🎤 Voice</button>
  <button class="tab" data-tab="phone">📱 Phone</button>
  <button class="tab" data-tab="gmail">📧 Gmail</button>
  <button class="tab" data-tab="system">🖥 System</button>
  <button class="tab" data-tab="smart">🧠 Smart</button>
  <button class="tab" data-tab="biometric">🔐 Auth</button>
  <button class="tab" data-tab="settings">⚙ Settings</button>
</nav>

<div class="main">
<div class="panel-col">

<!-- ══ CHAT ══ -->
<div class="panel card active" id="panel-chat">
  <div class="chat-scroll" id="chat-scroll">
    <div class="msg system">J.A.R.V.I.S. v6 · 7 AI providers · Gmail · Biometric · Voice · Phone · Smart Features<br>
    ⚙ Settings → add API keys &nbsp;|&nbsp; 🧠 Memory → index folders &nbsp;|&nbsp; ⚡ Macros → automate workflows</div>
  </div>
  <div class="composer">
    <div class="composer-attachments" id="ca"></div>
    <div class="composer-row">
      <button class="icon-btn" id="attach-btn" title="Attach">📎</button>
      <input type="file" id="file-input" multiple hidden>
      <textarea id="inp" rows="1" placeholder="Message J.A.R.V.I.S.… (Shift+Enter = newline)"></textarea>
      <button class="icon-btn active" id="mic-btn2" title="Voice">🎤</button>
      <button class="btn" id="send-btn">Send</button>
    </div>
    <p class="hint" id="voice-hint" style="margin-top:6px;min-height:14px"></p>
  </div>
</div>

<!-- ══ TASKS ══ -->
<div class="panel pscroll" id="panel-tasks">
  <div style="display:flex;gap:8px;margin-bottom:10px">
    <input class="inp" id="task-inp" placeholder="Something for J.A.R.V.I.S. to do…" style="flex:1">
    <button class="btn" onclick="addTask()">Add</button>
  </div>
  <p class="hint" style="margin-bottom:10px">Hit <b>Run</b> to send a task to Chat.</p>
  <div id="task-list"><p class="hint">No tasks yet.</p></div>
</div>

<!-- ══ FILES ══ -->
<div class="panel pscroll" id="panel-files">
  <div style="margin-bottom:12px">
    <button class="btn" onclick="document.getElementById('files-inp').click()">Upload Files</button>
    <input type="file" id="files-inp" multiple hidden>
  </div>
  <p class="hint" style="margin-bottom:10px">Uploaded files land in <code style="color:var(--accent)">uploads/</code>.</p>
  <div id="file-list"><p class="hint">No files yet.</p></div>
</div>

<!-- ══ MEMORY VAULT ══ -->
<div class="panel pscroll" id="panel-vault">
  <div class="eyebrow" style="margin-bottom:12px">🧠 Memory Vault — Local Knowledge RAG</div>
  <div class="lcard" style="margin-bottom:12px">
    <div class="eyebrow">Index a Folder</div>
    <div class="field-label">Folder Path</div>
    <input class="inp" id="vault-folder" placeholder="C:\Users\you\Notes or ~/projects/myapp" style="margin-bottom:6px">
    <div class="field-label">Vault Name (optional)</div>
    <input class="inp" id="vault-name" placeholder="school-notes">
    <div style="display:flex;align-items:center;gap:10px;margin-top:8px">
      <button class="btn" onclick="indexVault()">Index Folder</button>
      <span class="hint" id="vault-hint"></span>
    </div>
  </div>
  <div class="lcard" style="margin-bottom:12px">
    <div class="eyebrow">Search Vaults</div>
    <div style="display:flex;gap:8px;margin-top:8px">
      <input class="inp" id="vault-q" placeholder="Search your notes…" style="flex:1">
      <button class="btn" onclick="searchVault()">Search</button>
    </div>
    <div id="vault-results" style="margin-top:10px"></div>
  </div>
  <div class="eyebrow" style="margin-bottom:8px">Indexed Vaults</div>
  <div id="vault-list"><p class="hint">No vaults yet.</p></div>
</div>

<!-- ══ MACROS ══ -->
<div class="panel pscroll" id="panel-macros">
  <div class="eyebrow" style="margin-bottom:12px">⚡ Macros — Saved Action Sequences</div>
  <div class="lcard" style="margin-bottom:12px">
    <div class="eyebrow">Quick Create via Chat</div>
    <div style="display:flex;gap:8px;margin-top:8px">
      <input class="inp" id="macro-prompt" placeholder='"Save a macro: open Spotify, set volume 30"' style="flex:1">
      <button class="btn" onclick="macroPrompt()">Ask JARVIS</button>
    </div>
  </div>
  <div class="eyebrow" style="margin-bottom:8px">Saved Macros</div>
  <div id="macro-list"><p class="hint">No macros saved yet.</p></div>
</div>

<!-- ══ NOTIFICATIONS (ALERTS) ══ -->
<div class="panel pscroll" id="panel-notifications">
  <p class="hint" style="margin-bottom:10px">Risky actions pause here. Nothing runs until you approve.</p>
  <div id="notif-list"><p class="hint">No alerts yet.</p></div>
</div>

<!-- ══ HISTORY ══ -->
<div class="panel pscroll" id="panel-history">
  <p class="hint" style="margin-bottom:10px">Every chat auto-saves. Click to reopen.</p>
  <div id="chats-list"><p class="hint">No saved chats yet.</p></div>
</div>

<!-- ══ CORE ══ -->
<div class="panel" id="panel-core" style="align-items:center;justify-content:center;gap:28px;
  background:rgba(3,9,20,.5);backdrop-filter:var(--blur);border:1px solid var(--rim);border-radius:var(--r);padding:40px 24px">
  <div style="display:flex;flex-direction:column;align-items:center;gap:14px">
    <svg id="core-svg" viewBox="0 0 200 200" width="260" height="260" overflow="visible">
      <defs><radialGradient id="cg" cx="50%" cy="50%" r="50%">
        <stop offset="0%" stop-color="#3fd8e8" stop-opacity="1"/>
        <stop offset="100%" stop-color="#1f7684" stop-opacity="0.15"/>
      </radialGradient></defs>
      <circle cx="100" cy="100" r="94" fill="none" stroke="rgba(63,216,232,.10)" stroke-width="1"/>
      <circle id="core-dot-ring" cx="100" cy="100" r="70" fill="none" stroke="#0ea5c8" stroke-width="1.5"
        stroke-dasharray="1.5 5" style="transform-origin:100px 100px;animation:spin 25s linear infinite"/>
      <circle id="core-arc" cx="100" cy="100" r="52" fill="none" stroke="#3fd8e8" stroke-width="2.8"
        stroke-dasharray="18 12" style="transform-origin:100px 100px;animation:spin 10s linear infinite reverse;
        filter:drop-shadow(0 0 4px rgba(63,216,232,.5))"/>
      <circle cx="100" cy="100" r="24" fill="url(#cg)"
        style="filter:drop-shadow(0 0 14px rgba(63,216,232,.75)) drop-shadow(0 0 30px rgba(63,216,232,.25));animation:corebreathe 4s ease-in-out infinite"/>
    </svg>
    <div id="core-caption" class="eyebrow" style="letter-spacing:.25em">idle</div>
  </div>
  <p id="jarvis-caption" style="max-width:580px;text-align:center;font-size:17px;line-height:1.75;
    color:var(--text);text-shadow:0 0 40px rgba(63,216,232,.18)">Ask me something or give me a task.</p>
</div>

<!-- ══ VOICE ══ -->
<div class="panel pscroll" id="panel-voice">
  <div class="eyebrow" style="margin-bottom:12px">🎤 Voice System</div>
  <div class="stat-grid">
    <div class="stat-tile"><div class="lbl">Status</div><div class="val" id="v-status" style="font-size:13px;margin-top:5px">Ready</div></div>
    <div class="stat-tile"><div class="lbl">Language</div><div class="val" id="v-lang" style="font-size:13px;margin-top:5px">en-US</div></div>
  </div>
  <div class="lcard" style="margin-bottom:12px">
    <div class="eyebrow">Settings</div>
    <div class="field-label">Recognition Language</div>
    <select class="inp" id="lang-sel" style="margin-bottom:6px">
      <option value="en-US">English (US)</option><option value="en-GB">English (UK)</option>
      <option value="es-ES">Spanish</option><option value="fr-FR">French</option>
      <option value="de-DE">German</option><option value="it-IT">Italian</option>
      <option value="pt-BR">Portuguese</option><option value="zh-CN">Chinese</option>
      <option value="ja-JP">Japanese</option><option value="ko-KR">Korean</option>
    </select>
    <div class="field-label">TTS Voice</div>
    <select class="inp" id="tts-gender" style="margin-bottom:8px">
      <option value="female">Female</option><option value="male">Male</option>
    </select>
    <div style="display:flex;gap:7px;flex-wrap:wrap">
      <button class="btn" onclick="saveVoiceSettings()">Save</button>
      <button class="btn ghost" onclick="post('/api/v6/voice/hotword',{}).then(r=>log('Hotword: '+r.message,'ok'))">Start Hotword</button>
    </div>
  </div>
  <div class="lcard">
    <div class="eyebrow">Recent Voice Commands</div>
    <div id="voice-history" class="hint">None yet.</div>
  </div>
</div>

<!-- ══ PHONE ══ -->
<div class="panel pscroll" id="panel-phone">
  <div class="eyebrow" style="margin-bottom:12px">📱 Phone Integration (ADB)</div>
  <div class="lcard" style="margin-bottom:12px">
    <div class="eyebrow">Device Status</div>
    <div id="phone-status" class="hint">Click Refresh to check.</div>
    <button class="btn sm ghost" onclick="refreshPhone()" style="margin-top:8px">Refresh</button>
  </div>
  <div class="lcard" style="margin-bottom:12px">
    <div class="eyebrow">Send Message</div>
    <div class="field-label">Number</div>
    <input class="inp" id="sms-nr" placeholder="+1234567890" style="margin-bottom:6px">
    <div class="field-label">Message</div>
    <textarea class="inp" id="sms-body" rows="3" placeholder="Type message…"></textarea>
    <div style="display:flex;gap:7px;margin-top:8px">
      <button class="btn" onclick="sendSMS()">Send SMS</button>
      <button class="btn ghost" onclick="sendWA()">WhatsApp</button>
    </div>
  </div>
  <div class="lcard">
    <div class="eyebrow">Inbox</div>
    <div id="sms-list" class="hint">Click Read to load.</div>
    <button class="btn sm ghost" onclick="readSMS()" style="margin-top:8px">Read SMS</button>
  </div>
</div>

<!-- ══ GMAIL ══ -->
<div class="panel pscroll" id="panel-gmail">
  <div class="eyebrow" style="margin-bottom:12px">📧 Gmail Integration</div>

  <!-- Preview container -->
  <div id="gmail-email-preview" style="margin-top:10px;padding:10px;background:rgba(255,255,255,.04);border-radius:10px;display:none;"></div>

  <div class="lcard" style="margin-bottom:12px">
    <div class="eyebrow">Inbox</div>
    <div style="display:flex;gap:8px;margin-bottom:8px">
      <input class="inp" id="gmail-q" placeholder='Search: from:boss subject:meeting…' style="flex:1">
      <button class="btn sm" onclick="gmailSearch()">Search</button>
      <button class="btn sm ghost" onclick="gmailLoad()">Refresh</button>
    </div>
    <div id="gmail-list"><p class="hint">Click Refresh to load emails.</p></div>
  </div>

  <div class="lcard">
    <div class="eyebrow">Compose</div>
    <div class="field-label">To</div>
    <input class="inp" id="gmail-to" placeholder="recipient@email.com" style="margin-bottom:6px">
    <div class="field-label">Subject</div>
    <input class="inp" id="gmail-subj" placeholder="Subject" style="margin-bottom:6px">
    <div class="field-label">Body</div>
    <textarea class="inp" id="gmail-body" rows="4" placeholder="Email body…"></textarea>
    <div style="display:flex;gap:7px;margin-top:8px">
      <button class="btn" onclick="gmailSend()">Send Email</button>
      <button class="btn ghost sm" onclick="post('/api/v6/gmail/profile',{}).then(r=>log(r.email+' — '+r.total_msgs+' msgs','ok'))">Profile</button>
    </div>
  </div>
</div>  <!-- ← THIS CLOSING TAG IS CRUCIAL -->

<!-- ══ SYSTEM ══ -->
<div class="panel pscroll" id="panel-system">
  <div class="eyebrow" style="margin-bottom:12px">🖥 System Control & Monitoring</div>
  <div class="stat-grid">
    <div class="stat-tile"><div class="lbl">CPU</div><div class="val" id="s-cpu">—</div>
      <div class="pbar"><div class="pbar-fill" id="s-cpu-b" style="width:0%"></div></div></div>
    <div class="stat-tile"><div class="lbl">Memory</div><div class="val" id="s-mem">—</div>
      <div class="pbar"><div class="pbar-fill" id="s-mem-b" style="width:0%"></div></div></div>
    <div class="stat-tile"><div class="lbl">Disk</div><div class="val" id="s-disk">—</div>
      <div class="pbar"><div class="pbar-fill" id="s-disk-b" style="width:0%;background:var(--amber)"></div></div></div>
    <div class="stat-tile"><div class="lbl">Battery</div><div class="val" id="s-batt">—</div></div>
  </div>
  <div class="lcard" style="margin-bottom:12px">
    <div class="eyebrow">Quick Actions</div>
    <div style="display:flex;flex-wrap:wrap;gap:7px;margin-top:6px">
      <button class="btn sm ghost" onclick="post('/api/v6/app/open',{app:'notepad'})">Notepad</button>
      <button class="btn sm ghost" onclick="post('/api/v6/app/open',{app:'calc'})">Calculator</button>
      <button class="btn sm ghost" onclick="post('/api/v6/app/open',{app:'chrome'})">Chrome</button>
      <button class="btn sm ghost" onclick="refreshStats()">Refresh Stats</button>
    </div>
  </div>
  <div class="lcard"><div class="eyebrow">Running Apps</div><div id="app-list" class="hint" style="margin-top:6px">Click Refresh.</div></div>
</div>

<!-- ══ SMART ══ -->
<div class="panel pscroll" id="panel-smart">
  <div class="eyebrow" style="margin-bottom:12px">🧠 Smart Features</div>
  <div class="lcard" style="margin-bottom:12px">
    <div class="eyebrow">Proactive Suggestions</div>
    <div id="suggestions" class="hint" style="margin-top:6px">Click Refresh.</div>
    <button class="btn sm ghost" onclick="getSuggestions()" style="margin-top:8px">Refresh</button>
  </div>
  <div class="lcard" style="margin-bottom:12px">
    <div class="eyebrow">Emotion Detector</div>
    <div style="display:flex;gap:7px;margin-top:6px">
      <input class="inp" id="emo-inp" placeholder="Type to analyse emotion…" style="flex:1">
      <button class="btn sm" onclick="detectEmotion()">Analyse</button>
    </div>
    <div id="emo-result" style="margin-top:8px;font-family:var(--mono);font-size:12px;color:var(--text2)"></div>
  </div>
  <div class="lcard" style="margin-bottom:12px">
    <div class="eyebrow">History Search</div>
    <div style="display:flex;gap:7px;margin-top:6px">
      <input class="inp" id="hist-q" placeholder="Search command history…" style="flex:1">
      <button class="btn sm" onclick="searchHistory()">Search</button>
    </div>
    <div id="hist-results" style="margin-top:8px"></div>
  </div>
  <div class="lcard">
    <div class="eyebrow">Analytics</div>
    <div id="analytics" class="hint" style="margin-top:6px">Click Load.</div>
    <button class="btn sm ghost" onclick="loadAnalytics()" style="margin-top:8px">Load Analytics</button>
  </div>
</div>

<!-- ══ BIOMETRIC ══ -->
<div class="panel pscroll" id="panel-biometric">
  <div class="eyebrow" style="margin-bottom:12px">🔐 Biometric Authentication</div>
  <div class="lcard" style="margin-bottom:12px">
    <div class="eyebrow">Register User</div>
    <div class="field-label">User ID</div>
    <input class="inp" id="bio-uid" placeholder="e.g. kim" style="margin-bottom:8px">
    <div style="display:flex;gap:7px;flex-wrap:wrap">
      <button class="btn" onclick="bioRegister('face')">📸 Face</button>
      <button class="btn ghost" onclick="bioRegister('fingerprint')">👆 Fingerprint</button>
      <button class="btn ghost" onclick="bioRegister('face,fingerprint')">🔐 Both</button>
    </div>
  </div>
  <div class="lcard" style="margin-bottom:12px">
    <div class="eyebrow">Authenticate</div>
    <div style="display:flex;gap:7px;flex-wrap:wrap;margin-top:6px">
      <button class="btn" onclick="bioAuth('any')">🔓 Any Method</button>
      <button class="btn ghost" onclick="bioAuth('face')">📸 Face</button>
      <button class="btn ghost" onclick="bioAuth('fingerprint')">👆 Fingerprint</button>
    </div>
    <div id="auth-result" style="margin-top:10px;font-family:var(--mono);font-size:12px"></div>
  </div>
  <div class="lcard">
    <div class="eyebrow">Status</div>
    <div id="bio-status" class="hint" style="margin-top:6px">Click Load.</div>
    <button class="btn sm ghost" onclick="bioStatus()" style="margin-top:8px">Load Status</button>
  </div>
</div>

<!-- ══ SETTINGS ══ -->
<div class="panel pscroll" id="panel-settings">
  <div class="eyebrow" style="margin-bottom:14px">⚙ Configuration</div>

  <!-- AI Providers -->
  <div class="lcard" style="margin-bottom:12px">
    <div class="eyebrow">AI Providers</div>
    <div class="ptabs" style="margin-top:8px">
      <button class="ptab active" data-pp="groq">Groq</button>
      <button class="ptab" data-pp="gemini">Gemini</button>
      <button class="ptab" data-pp="mistral">Mistral</button>
      <button class="ptab" data-pp="nvidia">NVIDIA</button>
      <button class="ptab" data-pp="openrouter">OpenRouter</button>
      <button class="ptab" data-pp="freellmapi">FreeLLMAPI</button>
      <button class="ptab" data-pp="ollama">Ollama</button>
    </div>

    <div class="ppane active" id="pp-groq">
      <div class="field-label">Groq API Key <span style="color:var(--green);font-size:9px">(free — console.groq.com)</span></div>
      <input class="inp" id="cfg-groq-key" type="password" placeholder="gsk_…">
      <div class="field-label">Model</div>
      <input class="inp" id="cfg-groq-model" placeholder="mixtral-8x7b-32768">
    </div>
    <div class="ppane" id="pp-gemini">
      <div class="field-label">Gemini API Key <span style="color:var(--green);font-size:9px">(free — makersuite.google.com)</span></div>
      <input class="inp" id="cfg-gemini-key" type="password" placeholder="AIza…">
      <div class="field-label">Model</div>
      <input class="inp" id="cfg-gemini-model" placeholder="gemini-1.5-flash">
    </div>
    <div class="ppane" id="pp-mistral">
      <div class="field-label">Mistral API Key <span style="color:var(--green);font-size:9px">(console.mistral.ai)</span></div>
      <input class="inp" id="cfg-mistral-key" type="password" placeholder="your-mistral-key">
      <div class="field-label">Model</div>
      <input class="inp" id="cfg-mistral-model" placeholder="mistral-small-latest">
    </div>
    <div class="ppane" id="pp-nvidia">
      <div class="field-label">NVIDIA API Key <span style="color:var(--green);font-size:9px">(build.nvidia.com)</span></div>
      <input class="inp" id="cfg-nvidia-key" type="password" placeholder="nvapi-…">
      <div class="field-label">Model</div>
      <input class="inp" id="cfg-nvidia-model" placeholder="meta/llama-3.1-70b-instruct">
    </div>
    <div class="ppane" id="pp-openrouter">
      <div class="field-label">OpenRouter API Keys <span style="color:var(--accent);font-size:9px">(multiple — round-robin)</span></div>
      <textarea class="inp" id="cfg-or-keys" rows="3" placeholder="sk-or-key1&#10;sk-or-key2&#10;sk-or-key3"></textarea>
      <div class="field-label">Model</div>
      <input class="inp" id="cfg-or-model" placeholder="openai/gpt-4o-mini">
    </div>
    <div class="ppane" id="pp-freellmapi">
      <div class="field-label">FreeLLMAPI Key</div>
      <input class="inp" id="cfg-fll-key" type="password" placeholder="your-key">
      <div class="field-label">Base URL</div>
      <input class="inp" id="cfg-fll-url" placeholder="http://localhost:8000">
      <div class="field-label">Model</div>
      <input class="inp" id="cfg-fll-model" placeholder="gemini-2.0-flash">
    </div>
    <div class="ppane" id="pp-ollama">
      <div class="field-label">Ollama Base URL</div>
      <input class="inp" id="cfg-oll-url" placeholder="http://localhost:11434">
      <div class="field-label">Model</div>
      <input class="inp" id="cfg-oll-model" placeholder="llama3.1">
    </div>

    <div class="field-label" style="margin-top:10px">Primary AI Provider</div>
    <select class="inp" id="cfg-primary">
      <option value="groq">Groq</option><option value="gemini">Gemini</option>
      <option value="mistral">Mistral</option><option value="nvidia">NVIDIA</option>
      <option value="openrouter">OpenRouter</option>
      <option value="freellmapi">FreeLLMAPI</option><option value="ollama">Ollama</option>
    </select>
    <div class="field-label">Personality</div>
    <select class="inp" id="cfg-persona">
      <option value="jarvis">J.A.R.V.I.S.</option>
      <option value="professional">Professional</option>
      <option value="friendly">Friendly</option>
      <option value="technical">Technical Expert</option>
      <option value="creative">Creative</option>
    </select>
  </div>

  <!-- Gmail -->
  <div class="lcard" style="margin-bottom:12px">
    <div class="eyebrow">Gmail (OAuth2)</div>
    <p class="hint" style="margin:6px 0">Place <code style="color:var(--accent)">credentials.json</code> (OAuth Desktop App) in
    <code style="color:var(--accent)">gmail_data/</code> folder, then click Connect.</p>
    <button class="btn" onclick="post('/api/v6/gmail/connect',{}).then(r=>log(r.message||r.error, r.ok?'ok':'fail'))">Connect Gmail</button>
  </div>

  <!-- Features -->
  <div class="lcard" style="margin-bottom:12px">
    <div class="eyebrow">Features</div>
    <div class="toggle-row"><label>Emotion Detection</label>
      <label class="toggle"><input type="checkbox" id="t-emotion" checked><span class="tslider"></span></label></div>
    <div class="toggle-row"><label>Proactive Suggestions</label>
      <label class="toggle"><input type="checkbox" id="t-proactive" checked><span class="tslider"></span></label></div>
    <div class="toggle-row"><label>Biometric Auth</label>
      <label class="toggle"><input type="checkbox" id="t-bio" checked><span class="tslider"></span></label></div>
    <div class="toggle-row"><label>Phone Integration</label>
      <label class="toggle"><input type="checkbox" id="t-phone" checked><span class="tslider"></span></label></div>
    <div class="toggle-row"><label>Auto-start at Boot</label>
      <label class="toggle"><input type="checkbox" id="t-autostart"><span class="tslider"></span></label></div>
  </div>

  <button class="btn" onclick="saveSettings()" style="width:100%">💾 Save Settings</button>
</div>

</div><!-- /panel-col -->

<!-- SIDEBAR -->
<aside class="sidebar">
  <div class="sb-block">
    <div class="eyebrow">system</div>
    <div class="sys-row"><span>CPU</span><span id="sb-cpu">—</span></div>
    <div class="sys-row"><span>Memory</span><span id="sb-mem">—</span></div>
    <div class="sys-row"><span>Battery</span><span id="sb-batt">—</span></div>
  </div>
  <div class="sb-block grow">
    <div class="eyebrow">activity log</div>
    <div class="log-list" id="log-list"></div>
  </div>
</aside>
</div><!-- /main -->
</div><!-- /frame -->

<style>
@keyframes spin{to{transform:rotate(360deg)}}
@keyframes corebreathe{
  0%,100%{filter:drop-shadow(0 0 12px rgba(63,216,232,.7)) drop-shadow(0 0 26px rgba(63,216,232,.22))}
  50%{filter:drop-shadow(0 0 20px rgba(63,216,232,.95)) drop-shadow(0 0 44px rgba(63,216,232,.4))}}
</style>
<script>
const socket=io();
let convId=localStorage.getItem('jv6_conv')||null;
let tasks=[],pendingFiles=[],micActive=false,mRec=null,chunks=[];

/* ── Socket ── */
socket.on('connect',()=>setConn(true));
socket.on('disconnect',()=>setConn(false));
socket.on('stats_update',applyStats);
socket.on('log_event',d=>log(d.text,d.cls));
function setConn(ok){
  document.getElementById('conn-led').className='led '+(ok?'on':'off');
  document.getElementById('conn-text').textContent=ok?'Online':'Offline';
}

/* ── Tabs ── */
document.querySelectorAll('.tab').forEach(t=>t.addEventListener('click',()=>switchTab(t.dataset.tab)));
function switchTab(name){
  document.querySelectorAll('.tab').forEach(x=>x.classList.toggle('active',x.dataset.tab===name));
  document.querySelectorAll('.panel').forEach(x=>x.classList.toggle('active',x.id==='panel-'+name));
  if(name==='notifications') refreshNotifs();
  if(name==='history')       refreshHistory();
  if(name==='files')         refreshFiles();
  if(name==='tasks')         refreshTasks();
  if(name==='vault')         refreshVaults();
  if(name==='macros')        refreshMacros();
  if(name==='system')        refreshStats();
  if(name==='smart')         getSuggestions();
  if(name==='phone')         refreshPhone();
  if(name==='gmail')         gmailLoad();
}

/* ── Chat ── */
const scroll=document.getElementById('chat-scroll');
const inp=document.getElementById('inp');
const sendB=document.getElementById('send-btn');
inp.addEventListener('input',()=>{inp.style.height='auto';inp.style.height=Math.min(inp.scrollHeight,140)+'px'});
inp.addEventListener('keydown',e=>{if(e.key==='Enter'&&!e.shiftKey){e.preventDefault();sendMsg()}});
sendB.addEventListener('click',sendMsg);

function addMsg(role,text){
  const el=document.createElement('div');
  el.className='msg '+role; el.textContent=text;
  scroll.appendChild(el); scroll.scrollTop=scroll.scrollHeight; return el;
}
function addNote(text){
  const el=document.createElement('div');
  el.className='msg action-note'; el.textContent=text;
  scroll.appendChild(el); scroll.scrollTop=scroll.scrollHeight;
}
let typEl=null;
function showTyping(){if(typEl)return;typEl=document.createElement('div');typEl.className='msg assistant';
  typEl.innerHTML='<div class="typing"><span></span><span></span><span></span></div>';
  scroll.appendChild(typEl);scroll.scrollTop=scroll.scrollHeight}
function hideTyping(){if(typEl){typEl.remove();typEl=null}}

async function sendMsg(){
  const text=inp.value.trim();
  if(!text&&!pendingFiles.length)return;
  const fileIds=pendingFiles.map(f=>f.id);
  const fileNames=pendingFiles.map(f=>f.name);
  inp.value='';inp.style.height='auto';
  pendingFiles=[];renderChips();
  let display=text;
  if(fileNames.length) display+=(display?'\n':'')+'📎 '+fileNames.join(', ');
  addMsg('user',display);
  sendB.disabled=true; showTyping();
  // Emotion detect quietly
  if(text){post('/api/v6/smart/emotion',{text}).then(r=>{
    if(r.emotion&&r.emotion!=='neutral'){
      const last=scroll.querySelector('.msg.user:last-child');
      if(last) last.innerHTML+=`<span class="ebadge emo-${r.emotion}">${r.emotion}</span>`;
    }
  }).catch(()=>{})}
  try{
    const r=await post('/api/chat',{message:text,conversation_id:convId,attachment_ids:fileIds});
    hideTyping();
    if(r.conversation_id){convId=r.conversation_id;localStorage.setItem('jv6_conv',convId)}
    if(r.type==='final'){addMsg('assistant',r.message||'(no response)');log('AI replied','ok');updateCoreCaption(r.message)}
    else if(r.type==='error'){addMsg('error','Error: '+(r.message||'?'))}
    else if(r.type==='confirm'){
      addNote('🔔 Needs approval — "'+humanize(r.name)+'". Switched to Alerts.');
      refreshNotifs(); switchTab('notifications');
    }
  }catch(e){hideTyping();addMsg('error','Cannot reach JARVIS server.')}
  sendB.disabled=false;
}

function humanize(s){return (s||'').replace(/_/g,' ')}

/* new chat */
document.getElementById('new-chat-btn').addEventListener('click',()=>{
  convId=null;localStorage.removeItem('jv6_conv');
  scroll.innerHTML='';addNote('New chat started.');
});

/* ── Attachments ── */
document.getElementById('attach-btn').addEventListener('click',()=>document.getElementById('file-input').click());
document.getElementById('file-input').addEventListener('change',async()=>{
  const ff=document.getElementById('file-input').files;
  if(!ff.length)return;
  const fd=new FormData();for(const f of ff)fd.append('files',f);
  const r=await fetch('/api/upload',{method:'POST',body:fd}).then(x=>x.json());
  if(r.ok){r.files.forEach(f=>pendingFiles.push(f));renderChips();log('Uploaded '+r.files.length+' file(s)','ok')}
  document.getElementById('file-input').value='';
});
function renderChips(){
  const ca=document.getElementById('ca');
  ca.innerHTML=pendingFiles.map((f,i)=>`<div class="chip">📎 ${f.name}
    <button onclick="pendingFiles.splice(${i},1);renderChips()">×</button></div>`).join('');
}

/* ── Voice ── */
[document.getElementById('mic-btn'),document.getElementById('mic-btn2')].forEach(b=>b.addEventListener('click',toggleMic));
async function toggleMic(){
  if(micActive){if(mRec&&mRec.state!=='inactive')mRec.stop();return}
  try{
    const stream=await navigator.mediaDevices.getUserMedia({audio:true});
    mRec=new MediaRecorder(stream);chunks=[];
    mRec.ondataavailable=e=>{if(e.data.size>0)chunks.push(e.data)};
    mRec.onstop=async()=>{
      const blob=new Blob(chunks,{type:'audio/webm'});
      stream.getTracks().forEach(t=>t.stop());
      setMicUI(false);
      document.getElementById('voice-hint').textContent='Transcribing…';
      const fd=new FormData();fd.append('audio',blob,'speech.webm');
      const r=await fetch('/api/transcribe',{method:'POST',body:fd}).then(x=>x.json());
      if(r.ok&&r.text){
        inp.value=(inp.value?inp.value+' ':'')+r.text;
        inp.style.height='auto';inp.style.height=Math.min(inp.scrollHeight,140)+'px';
        document.getElementById('voice-hint').textContent='';
        const vh=document.getElementById('voice-history');
        vh.innerHTML=`<div class="lcard" style="font-family:var(--mono);font-size:11.5px">${r.text}</div>`+vh.innerHTML;
        log('Voice: "'+r.text.slice(0,40)+'"','ok');
      } else document.getElementById('voice-hint').textContent=r.error||'Nothing heard.';
    };
    mRec.start(); micActive=true; setMicUI(true);
    document.getElementById('voice-hint').textContent='Listening… click to stop';
    setTimeout(()=>{if(micActive&&mRec&&mRec.state!=='inactive')mRec.stop()},15000);
  }catch(e){document.getElementById('voice-hint').textContent='Mic denied: '+e.message}
}
function setMicUI(on){
  micActive=on;
  [document.getElementById('mic-btn'),document.getElementById('mic-btn2')].forEach(b=>{
    b.classList.toggle('active',on);b.textContent=on?'⏹':'🎤';
  });
}
function saveVoiceSettings(){
  const lang=document.getElementById('lang-sel').value;
  document.getElementById('v-lang').textContent=lang;
  post('/api/config',{voice:{default_language:lang,tts_gender:document.getElementById('tts-gender').value}});
  log('Voice settings saved','ok');
}

/* ── Stats ── */
function applyStats(i){
  const cpu=i.cpu_percent??i.cpu?.usage_percent??null;
  const mem=i.memory_percent??i.memory?.used_percent??null;
  const disk=i.disk?.used_percent??null;
  const batt=i.battery_percent??null;
  if(cpu!=null){set('sb-cpu',cpu+'%');set('s-cpu',cpu+'%');bar('s-cpu-b',cpu)}
  if(mem!=null){set('sb-mem',mem+'%');set('s-mem',mem+'%');bar('s-mem-b',mem)}
  if(disk!=null){set('s-disk',disk+'%');bar('s-disk-b',disk)}
  if(batt!=null) set('sb-batt',batt+(i.battery_plugged?' ⚡':'')+'%');
}
function set(id,v){const el=document.getElementById(id);if(el)el.textContent=v}
function bar(id,v){const el=document.getElementById(id);if(el)el.style.width=v+'%'}
async function refreshStats(){
  const r=await fetch('/api/system-info').then(x=>x.json()).catch(()=>({}));
  if(r.ok)applyStats(r.info);
  const ra=await post('/api/v6/app/list',{});
  if(ra.apps){
    set('app-list','');
    const el=document.getElementById('app-list');
    el.innerHTML=ra.apps.slice(0,15).map(a=>
      `<div class="lcard" style="display:flex;justify-content:space-between;padding:8px 12px">
         <span style="font-size:12.5px">${a.name}</span>
         <span style="font-family:var(--mono);font-size:11px;color:var(--muted)">${a.memory_mb}MB</span>
       </div>`).join('');
  }
}

/* ── Tasks ── */
async function refreshTasks(){
  const r=await fetch('/api/tasks').then(x=>x.json()).catch(()=>({tasks:[]}));
  renderTasks(r.tasks||[]);
}
function renderTasks(items){
  const el=document.getElementById('task-list');
  if(!items.length){el.innerHTML='<p class="hint">No tasks yet.</p>';return}
  el.innerHTML=items.map(t=>`
    <div class="lcard task-card ${t.done?'done':''}" style="display:flex;align-items:center;gap:9px;margin-bottom:7px">
      <input type="checkbox" ${t.done?'checked':''} onchange="toggleTask('${t.id}',this.checked)" style="width:14px;height:14px;accent-color:var(--accent);flex:none">
      <span class="task-text" style="flex:1;font-size:13px">${t.text}</span>
      <div style="display:flex;gap:5px;flex:none">
        <button class="btn sm" onclick="runTask('${t.text}')">Run</button>
        <button class="btn sm ghost" onclick="deleteTask('${t.id}')">Del</button>
      </div>
    </div>`).join('');
}
async function addTask(){
  const v=document.getElementById('task-inp').value.trim();if(!v)return;
  document.getElementById('task-inp').value='';
  await post('/api/tasks',{text:v},true);refreshTasks();
}
document.getElementById('task-inp').addEventListener('keydown',e=>{if(e.key==='Enter')addTask()});
async function toggleTask(id,done){await fetch('/api/tasks/'+id,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({done})});refreshTasks()}
async function deleteTask(id){await fetch('/api/tasks/'+id,{method:'DELETE'});refreshTasks()}
function runTask(text){switchTab('chat');inp.value=text;inp.style.height='auto';inp.style.height=Math.min(inp.scrollHeight,140)+'px';sendMsg()}

/* ── Files ── */
document.getElementById('files-inp').addEventListener('change',async()=>{
  const ff=document.getElementById('files-inp').files;if(!ff.length)return;
  const fd=new FormData();for(const f of ff)fd.append('files',f);
  const r=await fetch('/api/upload',{method:'POST',body:fd}).then(x=>x.json());
  log('Uploaded '+r.files?.length+' file(s)',r.ok?'ok':'fail');
  document.getElementById('files-inp').value='';refreshFiles();
});
async function refreshFiles(){
  const r=await fetch('/api/uploads').then(x=>x.json()).catch(()=>({files:[]}));
  const el=document.getElementById('file-list');
  const files=r.files||[];
  if(!files.length){el.innerHTML='<p class="hint">No files yet.</p>';return}
  el.innerHTML=files.map(f=>`
    <div class="lcard" style="display:flex;align-items:center;gap:10px;margin-bottom:7px">
      <span style="font-size:18px">${f.category==='image'?'🖼️':f.category==='pdf'?'📕':f.category==='docx'?'📘':'📄'}</span>
      <div style="flex:1;min-width:0">
        <div style="font-size:13px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis">${f.name}</div>
        <div style="font-family:var(--mono);font-size:10.5px;color:var(--muted);margin-top:2px">${humanSize(f.size)} · ${f.category}</div>
      </div>
    </div>`).join('');
}
function humanSize(n){const u=['B','KB','MB','GB'];let i=0;n=Number(n)||0;while(n>=1024&&i<3){n/=1024;i++}return n.toFixed(i?1:0)+u[i]}

/* ── Vault ── */
async function refreshVaults(){
  const r=await fetch('/api/vaults').then(x=>x.json()).catch(()=>({vaults:[]}));
  const el=document.getElementById('vault-list');
  const vaults=r.vaults||[];
  if(!vaults.length){el.innerHTML='<p class="hint">No vaults yet.</p>';return}
  el.innerHTML=vaults.map(v=>`
    <div class="lcard" style="margin-bottom:7px">
      <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:4px">
        <span style="font-size:13px;font-weight:700;color:var(--accent)">🧠 ${v.name}</span>
        <span class="vbadge ${v.backend==='faiss'?'green':''}">${v.backend||'keyword'}</span>
      </div>
      <div style="font-family:var(--mono);font-size:10.5px;color:var(--muted);margin-bottom:4px">${v.folder}</div>
      <div style="font-family:var(--mono);font-size:10.5px;color:var(--muted);margin-bottom:8px">${v.file_count} files · ${v.chunk_count} chunks</div>
      <div style="display:flex;gap:6px">
        <button class="btn sm" onclick="document.getElementById('vault-q').value='';document.getElementById('vault-q').focus()">Search</button>
        <button class="btn sm ghost danger" onclick="deleteVault('${v.name}')">Delete</button>
      </div>
    </div>`).join('');
}
async function indexVault(){
  const folder=document.getElementById('vault-folder').value.trim();
  if(!folder){document.getElementById('vault-hint').textContent='Enter a path.';return}
  document.getElementById('vault-hint').textContent='Indexing…';
  const r=await post('/api/vaults',{folder_path:folder,vault_name:document.getElementById('vault-name').value.trim()},true);
  document.getElementById('vault-hint').textContent=r.ok?('✓ '+r.message):('Error: '+r.error);
  if(r.ok){refreshVaults();log('Vault indexed: '+r.vault,'ok')}
}
async function searchVault(){
  const q=document.getElementById('vault-q').value.trim();if(!q)return;
  const r=await fetch('/api/vaults/__all__/query',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({question:q,top_k:5})}).then(x=>x.json());
  const el=document.getElementById('vault-results');
  if(r.ok&&r.results?.length){
    el.innerHTML=r.results.map(x=>`<div class="lcard" style="margin-bottom:6px">
      <div style="font-family:var(--mono);font-size:10px;color:var(--accent2);margin-bottom:4px">📄 ${x.source}</div>
      <div style="font-size:12.5px">${esc(x.text.trim().slice(0,350))}…</div></div>`).join('');
  } else el.innerHTML='<p class="hint">'+(r.error||'No results.')+'</p>';
}
async function deleteVault(name){
  if(!confirm('Delete vault "'+name+'"?'))return;
  const r=await fetch('/api/vaults/'+encodeURIComponent(name),{method:'DELETE'}).then(x=>x.json());
  log('Vault deleted: '+name,'fail');refreshVaults();
}

/* ── Macros ── */
async function refreshMacros(){
  const r=await fetch('/api/macros').then(x=>x.json()).catch(()=>({macros:[]}));
  const el=document.getElementById('macro-list');
  const macros=r.macros||[];
  if(!macros.length){el.innerHTML='<p class="hint">No macros yet. Ask JARVIS to save one.</p>';return}
  el.innerHTML=macros.map(m=>`
    <div class="lcard" style="margin-bottom:7px">
      <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:4px">
        <span style="font-size:13px;font-weight:700;color:var(--amber)">⚡ ${m.name}</span>
        <span class="vbadge">${m.steps?.length||0} steps</span>
      </div>
      ${m.description?`<div style="font-size:12px;color:var(--muted);margin-bottom:6px">${m.description}</div>`:''}
      <div style="display:flex;gap:6px;flex-wrap:wrap">
        <button class="btn sm amber" onclick="runMacroDirect('${m.name}')">▶ Run</button>
        <button class="btn sm ghost" onclick="switchTab('chat');inp.value='Run my &quot;${m.name}&quot; macro';sendMsg()">Via Chat</button>
        <button class="btn sm ghost danger" onclick="deleteMacro('${m.name}')">Delete</button>
      </div>
    </div>`).join('');
}
async function macroPrompt(){
  const txt=document.getElementById('macro-prompt').value.trim();if(!txt)return;
  document.getElementById('macro-prompt').value='';
  switchTab('chat');inp.value=txt;sendMsg();
}
async function runMacroDirect(name){
  addNote('▶ Running macro "'+name+'"…');
  const r=await fetch('/api/macros/'+encodeURIComponent(name)+'/run',{method:'POST'}).then(x=>x.json());
  if(r.ok){
    const summary=r.step_results?.map(s=>s.tool+': '+(s.skipped?'⚠ skipped':s.result?.ok?'✓':'✗')).join(', ');
    addNote('✓ Macro done: '+summary);log('Macro ran: '+name,'ok');refreshMacros();
  } else addNote('✗ '+r.error);
}
async function deleteMacro(name){
  if(!confirm('Delete macro "'+name+'"?'))return;
  await fetch('/api/macros/'+encodeURIComponent(name),{method:'DELETE'});log('Macro deleted: '+name,'fail');refreshMacros();
}

/* ── Notifications ── */
async function refreshNotifs(){
  const r=await fetch('/api/notifications').then(x=>x.json()).catch(()=>({notifications:[]}));
  const items=r.notifications||[];
  const pending=items.filter(n=>n.status==='pending').length;
  document.getElementById('notif-badge').textContent=pending||'';
  const el=document.getElementById('notif-list');
  if(!items.length){el.innerHTML='<p class="hint">No alerts yet.</p>';return}
  el.innerHTML=items.map(n=>`
    <div class="lcard notif-card ${n.status}" style="margin-bottom:7px">
      <div style="display:flex;justify-content:space-between;font-family:var(--mono);font-size:12px;margin-bottom:5px">
        <span>${humanize(n.name)}</span>
        <span style="color:${n.status==='pending'?'var(--amber)':n.status==='approved'?'var(--accent)':'var(--muted)'}">${n.status}</span>
      </div>
      ${n.args&&Object.keys(n.args).length?`<pre style="font-family:var(--mono);font-size:11px;color:var(--accent);background:rgba(0,0,0,.4);padding:7px;border-radius:7px;margin-bottom:7px;overflow-x:auto">${esc(JSON.stringify(n.args,null,2))}</pre>`:''}
      ${n.status==='pending'?`
      <div style="display:flex;gap:7px">
        <button class="btn sm ghost" onclick="resolve('${n.id}','${n.conversation_id}',false)">Deny</button>
        <button class="btn sm danger" onclick="resolve('${n.id}','${n.conversation_id}',true)">Approve</button>
      </div>`:''}
    </div>`).join('');
}
async function resolve(nid,cid,approved){
  log(approved?'Approved':'Denied','ok');
  const same=cid===convId;
  if(same)showTyping();
  const r=await post('/api/confirm',{conversation_id:cid,approved});
  if(same){hideTyping();addNote((approved?'✔ approved':'✘ denied'));
    if(r.type==='final')addMsg('assistant',r.message||'');
  }
  refreshNotifs();
}

/* ── History ── */
async function refreshHistory(){
  const r=await fetch('/api/chats').then(x=>x.json()).catch(()=>({chats:[]}));
  const el=document.getElementById('chats-list');
  const chats=r.chats||[];
  if(!chats.length){el.innerHTML='<p class="hint">No saved chats yet.</p>';return}
  el.innerHTML=chats.slice(0,50).map(c=>`
    <div class="lcard" style="display:flex;justify-content:space-between;cursor:pointer;margin-bottom:7px"
         onclick="loadChat('${c.id}')">
      <span style="font-size:13px">${c.title||'(untitled)'}</span>
      <span style="font-family:var(--mono);font-size:10.5px;color:var(--muted)">${timeAgo(c.updated_at)}</span>
    </div>`).join('');
}
async function loadChat(id){
  const r=await fetch('/api/chats/'+id).then(x=>x.json());
  if(!r.ok)return;
  convId=id;localStorage.setItem('jv6_conv',convId);
  scroll.innerHTML='';
  (r.chat?.messages||[]).forEach(m=>{
    if(m.role==='user') addMsg('user',typeof m.content==='string'?m.content:(m.content?.find?.(b=>b.type==='text')?.text||''));
    else if(m.role==='assistant'&&m.content) addMsg('assistant',typeof m.content==='string'?m.content:'');
  });
  switchTab('chat');
}
function timeAgo(ts){const d=Date.now()/1000-ts;if(d<60)return 'now';if(d<3600)return Math.floor(d/60)+'m';if(d<86400)return Math.floor(d/3600)+'h';return new Date(ts*1000).toLocaleDateString()}

/* ── Core tab ── */
function updateCoreCaption(text){
  if(text) document.getElementById('jarvis-caption').textContent=text.slice(0,200);
}

/* ── Phone ── */
async function refreshPhone(){
  const r=await post('/api/v6/phone/status',{});
  document.getElementById('phone-status').textContent=r.device_connected?'✓ Device connected':'✗ No device — enable USB Debugging';
}
async function sendSMS(){
  const nr=document.getElementById('sms-nr').value.trim();
  const body=document.getElementById('sms-body').value.trim();
  if(!nr||!body)return;
  const r=await post('/api/v6/phone/sms/send',{phone_number:nr,message:body});
  log('SMS: '+(r.ok?'sent':'failed'),r.ok?'ok':'fail');
}
async function sendWA(){
  const nr=document.getElementById('sms-nr').value.trim();
  const body=document.getElementById('sms-body').value.trim();
  if(!nr||!body)return;
  const r=await post('/api/v6/phone/whatsapp/send',{phone_number:nr,message:body});
  log('WhatsApp: '+(r.ok?'ready':'failed'),r.ok?'ok':'fail');
}
async function readSMS(){
  const r=await post('/api/v6/phone/sms/read',{limit:10});
  const el=document.getElementById('sms-list');
  el.innerHTML=r.ok&&r.messages?.length
    ? r.messages.map(m=>`<div class="lcard" style="font-size:12.5px;margin-bottom:5px">${JSON.stringify(m)}</div>`).join('')
    : '<p class="hint">'+(r.error||'No messages.')+'</p>';
}

/* ── Gmail ── */
async function gmailLoad(){
document.getElementById('gmail-email-preview').style.display = 'none';
  const r=await post('/api/v6/gmail/list',{max_results:15});
  renderGmail(r);
}
async function gmailSearch(){
  const q = document.getElementById('gmail-q').value.trim();
  if(!q) return;
  document.getElementById('gmail-email-preview').style.display = 'none';
  const r = await post('/api/v6/gmail/search', {query: q, max_results: 15});
  renderGmail(r);
}
function renderGmail(r){
  const el = document.getElementById('gmail-list');
  if(!r.ok){
    el.innerHTML = '<p class="hint">' + (r.error || 'Gmail not connected. See Settings → Connect Gmail.') + '</p>';
    return;
  }
  let emails = r.emails || [];
  if(!emails.length){
    el.innerHTML = '<p class="hint">No emails found.</p>';
    return;
  }

  // Sort: unread first, then by date (newest first) within each group
  emails.sort((a, b) => {
    // Unread first
    if (a.unread && !b.unread) return -1;
    if (!a.unread && b.unread) return 1;
    // If same unread status, sort by date (newest first)
    return new Date(b.date) - new Date(a.date);
  });

  el.innerHTML = emails.map(e => `
    <div class="lcard" style="margin-bottom:7px; opacity: ${e.unread ? 1 : 0.6};">
      <div style="display:flex;justify-content:space-between;margin-bottom:3px;">
        <span style="font-size:12.5px;font-weight:${e.unread ? '700' : '400'}">${esc(e.subject)}</span>
        ${e.unread ? '<span style="color:var(--accent);font-family:var(--mono);font-size:10px;">UNREAD</span>' : ''}
      </div>
      <div style="font-family:var(--mono);font-size:10.5px;color:var(--muted);margin-bottom:4px;">${esc(e.from)}</div>
      <div style="font-size:12px;color:var(--text2)">${esc(e.snippet?.slice(0,120) || '')}…</div>
      <div style="display:flex;gap:6px;margin-top:7px;">
        <button class="btn sm ghost" onclick="gmailRead('${e.id}')">Read</button>
        <button class="btn sm ghost" onclick="gmailMarkRead('${e.id}')">Mark Read</button>
        <button class="btn sm ghost danger" onclick="gmailTrash('${e.id}')">Trash</button>
      </div>
    </div>
  `).join('');
}
async function gmailRead(id){
  console.log('[DEBUG] gmailRead called with id:', id);
  const r = await post('/api/v6/gmail/get', {email_id: id});
  console.log('[DEBUG] gmailRead response:', r);
  if(r.ok){
    const preview = document.getElementById('gmail-email-preview');
    preview.style.display = 'block';
    let bodyContent = r.body || '(No body)';
    
    // Detect if body contains HTML
    const isHtml = /<[a-z][\s\S]*>/i.test(bodyContent);
    
    // For plain text emails, just show text
    if(!isHtml){
      preview.innerHTML = `
        <div class="eyebrow">📧 ${esc(r.subject || '(no subject)')}</div>
        <div style="font-size:12px;color:var(--muted);margin:4px 0;">From: ${esc(r.from || '')}</div>
        <div style="font-size:12px;color:var(--muted);margin:4px 0;">Date: ${esc(r.date || '')}</div>
        <div style="font-family:var(--mono);font-size:13px;white-space:pre-wrap;margin-top:8px;padding:10px;background:rgba(0,0,0,.3);border-radius:8px;max-height:300px;overflow-y:auto;color:var(--text);">${esc(bodyContent)}</div>
      `;
      return;
    }
    
    // For HTML emails: create a container with both rendered and plain text views
    // Extract plain text from HTML using DOMParser
    const parser = new DOMParser();
    const doc = parser.parseFromString(bodyContent, 'text/html');
    const plainText = doc.body.textContent || '(No plain text extracted)';
    
    // Create a unique ID for this email preview
    const uid = 'email_' + Date.now();
    
    preview.innerHTML = `
      <div class="eyebrow">📧 ${esc(r.subject || '(no subject)')}</div>
      <div style="font-size:12px;color:var(--muted);margin:4px 0;">From: ${esc(r.from || '')}</div>
      <div style="font-size:12px;color:var(--muted);margin:4px 0;">Date: ${esc(r.date || '')}</div>
      <div style="margin-top:8px;">
        <div style="display:flex;gap:8px;margin-bottom:8px;">
          <button class="btn sm ghost" onclick="toggleEmailView('${uid}', 'html')">Rendered</button>
          <button class="btn sm ghost" onclick="toggleEmailView('${uid}', 'text')">Plain Text</button>
        </div>
        <div id="${uid}_html" style="display:block;">
          <iframe srcdoc="${`
            <!DOCTYPE html>
            <html>
              <head>
                <meta charset="utf-8">
                <style>
                  body { 
                    background: #020810; 
                    color: #e2f0f8; 
                    font-family: 'IBM Plex Sans', system-ui, sans-serif; 
                    padding: 16px; 
                    margin: 0; 
                    line-height: 1.6;
                  }
                  a { color: #3fd8e8; }
                  h1, h2, h3 { color: #e2f0f8; }
                  blockquote { border-left: 3px solid #3fd8e8; padding-left: 16px; margin-left: 0; color: #9ab8cc; }
                  img { max-width: 100%; }
                  /* Hide external images if blocked by iframe */
                </style>
              </head>
              <body>${bodyContent}</body>
            </html>
          `.replace(/"/g,'&quot;')}" style="width:100%;height:350px;border:none;border-radius:8px;background:#020810;"></iframe>
        </div>
        <div id="${uid}_text" style="display:none;font-family:var(--mono);font-size:13px;white-space:pre-wrap;padding:10px;background:rgba(0,0,0,.3);border-radius:8px;max-height:300px;overflow-y:auto;color:var(--text);">${esc(plainText)}</div>
      </div>
    `;
    
  } else {
    alert('Error reading email: ' + (r.error || 'Unknown error'));
  }
}

// Toggle function for HTML vs plain text view
function toggleEmailView(uid, view){
  const htmlEl = document.getElementById(uid + '_html');
  const textEl = document.getElementById(uid + '_text');
  if(view === 'html'){
    htmlEl.style.display = 'block';
    textEl.style.display = 'none';
  } else {
    htmlEl.style.display = 'none';
    textEl.style.display = 'block';
  }
}
async function gmailMarkRead(id){
  console.log('[DEBUG] gmailMarkRead called with id:', id);
  const r = await post('/api/v6/gmail/mark_read', {email_id: id});
  console.log('[DEBUG] gmailMarkRead response:', r);
  if(r.ok){
    gmailLoad(); // refresh list
  } else {
    alert('Error marking as read: ' + (r.error || 'Unknown error'));
    console.error('gmailMarkRead error:', r);
  }
}
async function gmailTrash(id){if(!confirm('Trash this email?'))return;await post('/api/v6/gmail/trash',{email_id:id});gmailLoad();log('Email trashed','warn')}
async function gmailSend(){
  const to=document.getElementById('gmail-to').value.trim();
  const subj=document.getElementById('gmail-subj').value.trim();
  const body=document.getElementById('gmail-body').value.trim();
  if(!to||!subj||!body){alert('Fill in all fields.');return}
  const r=await post('/api/v6/gmail/send',{to,subject:subj,body});
  log('Gmail send: '+(r.ok?'sent':'failed '+r.error),r.ok?'ok':'fail');
  if(r.ok){document.getElementById('gmail-to').value='';document.getElementById('gmail-subj').value='';document.getElementById('gmail-body').value='';alert('Email sent!')}
}

/* ── Smart ── */
async function getSuggestions(){
  const r=await post('/api/v6/smart/suggest',{});
  const el=document.getElementById('suggestions');
  el.innerHTML=r.ok&&r.suggestions?.length
    ? r.suggestions.map(s=>`<div class="lcard" style="margin-bottom:6px;font-size:12.5px">• ${s}</div>`).join('')
    : '<p class="hint">No suggestions.</p>';
}
async function detectEmotion(){
  const text=document.getElementById('emo-inp').value.trim();if(!text)return;
  const r=await post('/api/v6/smart/emotion',{text});
  document.getElementById('emo-result').innerHTML=r.ok
    ? `Emotion: <span class="ebadge emo-${r.emotion}">${r.emotion}</span>  ${Math.round((r.confidence||0)*100)}% confidence`
    : 'Error: '+r.error;
}
async function searchHistory(){
  const q=document.getElementById('hist-q').value.trim();if(!q)return;
  const r=await post('/api/v6/smart/history',{query:q,limit:10});
  document.getElementById('hist-results').innerHTML=r.ok&&r.results?.length
    ? r.results.map(h=>`<div class="lcard" style="margin-bottom:5px">
        <div style="font-family:var(--mono);font-size:10px;color:var(--muted)">${(h.timestamp||'').slice(0,16)}</div>
        <div style="font-size:12.5px;margin-top:3px">${esc(h.text||'')}</div></div>`).join('')
    : '<p class="hint">No results.</p>';
}
async function loadAnalytics(){
  const r=await post('/api/v6/smart/analytics',{});
  document.getElementById('analytics').innerHTML=r.ok
    ? `<div style="font-family:var(--mono);font-size:11.5px;line-height:1.9">
       Total: <b>${r.total_commands||0}</b> · Success: <b>${Math.round((r.success_rate||0)*100)}%</b><br>
       Top: <b>${r.top_category||'—'}</b> · Peak: <b>${r.busiest_hour||'—'}</b></div>`
    : '<p class="hint">Unavailable.</p>';
}

/* ── Biometric ── */
async function bioRegister(methods){
  const uid=document.getElementById('bio-uid').value.trim();if(!uid){alert('Enter User ID.');return}
  const r=await post('/api/v6/biometric/register',{user_id:uid,methods:methods.split(',')});
  document.getElementById('auth-result').textContent=JSON.stringify(r,null,2);
  log('Bio register: '+(r.ok?'ok':'fail'),r.ok?'ok':'fail');
}
async function bioAuth(method){
  const r=await post('/api/v6/biometric/authenticate',{method});
  const el=document.getElementById('auth-result');
  el.textContent=r.ok?'✓ Authenticated — '+r.detail:'✗ Failed — '+r.detail;
  el.style.color=r.ok?'var(--green)':'var(--danger)';
  log('Auth: '+(r.ok?'ok':'failed'),r.ok?'ok':'fail');
}
async function bioStatus(){
  const r=await post('/api/v6/biometric/status',{});
  document.getElementById('bio-status').innerHTML=r.ok
    ? `Face: ${r.face_auth?.available?'✓':'✗'}  Users: ${(r.face_auth?.status?.registered_users||[]).join(', ')||'none'}<br>
       Fingerprint: ${r.fingerprint_auth?.available?'✓':'✗'}`
    : r.error||'Unavailable';
}

/* ── Settings ── */
document.querySelectorAll('.ptab').forEach(t=>t.addEventListener('click',()=>{
  document.querySelectorAll('.ptab').forEach(x=>x.classList.remove('active'));
  document.querySelectorAll('.ppane').forEach(x=>x.classList.remove('active'));
  t.classList.add('active');
  document.getElementById('pp-'+t.dataset.pp).classList.add('active');
}));
async function saveSettings(){
  const or_keys=(document.getElementById('cfg-or-keys').value||'').split('\n').map(k=>k.trim()).filter(Boolean);
  const body={
    ai:{
      groq_api_key:   v('cfg-groq-key')||undefined,
      groq_model:     v('cfg-groq-model')||undefined,
      gemini_api_key: v('cfg-gemini-key')||undefined,
      gemini_model:   v('cfg-gemini-model')||undefined,
      mistral_api_key:v('cfg-mistral-key')||undefined,
      mistral_model:  v('cfg-mistral-model')||undefined,
      nvidia_api_key: v('cfg-nvidia-key')||undefined,
      nvidia_model:   v('cfg-nvidia-model')||undefined,
      openrouter_keys:or_keys.length?or_keys:undefined,
      openrouter_model:v('cfg-or-model')||undefined,
      freellmapi_key: v('cfg-fll-key')||undefined,
      freellmapi_url: v('cfg-fll-url')||undefined,
      freellmapi_model:v('cfg-fll-model')||undefined,
      ollama_url:     v('cfg-oll-url')||undefined,
      ollama_model:   v('cfg-oll-model')||undefined,
      primary:        v('cfg-primary'),
      personality:    v('cfg-persona'),
    },
    smart:{emotion_detection:document.getElementById('t-emotion').checked,
           proactive:document.getElementById('t-proactive').checked},
    biometric:{enabled:document.getElementById('t-bio').checked},
    phone:{enabled:document.getElementById('t-phone').checked},
    auto_start:{enabled:document.getElementById('t-autostart').checked},
  };
  const r=await post('/api/config',body,true);
  log('Settings saved',r.ok?'ok':'fail');
  alert(r.ok?'Settings saved!':'Error saving settings.');
}
function v(id){const el=document.getElementById(id);return el?el.value.trim():''}

/* ── Helpers ── */
async function post(url,body,isPatch=false){
  try{
    const r=await fetch(url,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)});
    return await r.json();
  }catch(e){return{ok:false,error:String(e)}}
}
function log(text,cls=''){
  const el=document.createElement('div');el.className='log-entry '+(cls||'');
  const t=new Date().toLocaleTimeString([],{hour:'2-digit',minute:'2-digit',second:'2-digit'});
  el.innerHTML=`<span class="log-t">${t}</span>${text}`;
  const list=document.getElementById('log-list');list.prepend(el);
  if(list.children.length>200)list.lastChild.remove();
}
function esc(s){return (s||'').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;')}

/* ── Init ── */
socket.on('stats_update',applyStats);
setInterval(()=>fetch('/api/system-info').then(r=>r.json()).then(d=>{if(d.ok)applyStats(d.info)}).catch(()=>{}),6000);
setInterval(refreshNotifs,5000);
refreshStats(); refreshTasks(); refreshVaults(); refreshMacros();
log('JARVIS v6 UI ready','ok');
</script>
</body>
</html>"""


# ─────────────────────────────────────────────────────────────
# Flask + SocketIO app
# ─────────────────────────────────────────────────────────────

class JarvisWebInterface:
    def __init__(self, host="127.0.0.1", port=5000, jarvis_core=None):
        self.host  = host
        self.port  = port
        self.core  = jarvis_core
        self.app   = Flask(__name__)
        self.app.config["SECRET_KEY"] = "jarvis-v6-web-secret"
        self.app.config["MAX_CONTENT_LENGTH"] = 200 * 1024 * 1024
        self.sio   = SocketIO(self.app, cors_allowed_origins="*")
        self._setup()
      
    def _setup(self):
        app, sio, iface = self.app, self.sio, self

        def core(): return iface.core

        # ── UI ────────────────────────────────────────────────
        @app.route("/")
        def index(): return render_template_string(HTML)

        # ── v5 compatibility endpoints ────────────────────────
        @app.route("/api/chat", methods=["POST"])
        def api_chat():
            from app import chat   # delegate to existing app.py handler
            return chat()

        @app.route("/api/config", methods=["GET", "POST"])
        def api_config():
            from app import get_config, set_config
            if request.method == "POST": return set_config()
            return get_config()

        @app.route("/api/system-info")
        def api_sysinfo():
            from app import system_info; return system_info()

        @app.route("/api/tasks",           methods=["GET","POST"])
        @app.route("/api/tasks/<tid>",     methods=["POST","DELETE"])
        @app.route("/api/upload",          methods=["POST"])
        @app.route("/api/uploads",         methods=["GET"])
        @app.route("/api/vaults",          methods=["GET","POST"])
        @app.route("/api/vaults/<n>",      methods=["DELETE"])
        @app.route("/api/vaults/<n>/query",methods=["POST"])
        @app.route("/api/vaults/__all__/query", methods=["POST"])
        @app.route("/api/macros",          methods=["GET","POST"])
        @app.route("/api/macros/<n>",      methods=["DELETE"])
        @app.route("/api/macros/<n>/run",  methods=["POST"])
        @app.route("/api/notifications",   methods=["GET"])
        @app.route("/api/confirm",         methods=["POST"])
        @app.route("/api/chats",           methods=["GET"])
        @app.route("/api/chats/<cid>",     methods=["GET"])
        @app.route("/api/transcribe",      methods=["POST"])
        def proxy_to_app(**kwargs):
            """Proxy all v5 routes to the app module's stub functions."""
            import app as app_mod
            from flask import current_app, jsonify, request

            path = request.path

            # ── Tasks ──────────────────────────────────────────────
            if path == "/api/tasks":
                return current_app.ensure_sync(app_mod.tasks)()
            elif path.startswith("/api/tasks/"):
                tid = path.split("/")[-1]
                return current_app.ensure_sync(app_mod.task_detail)(tid)

            # ── Uploads ────────────────────────────────────────────
            elif path == "/api/upload":
                return current_app.ensure_sync(app_mod.upload)()
            elif path == "/api/uploads":
                return current_app.ensure_sync(app_mod.uploads)()

            # ── Vaults ─────────────────────────────────────────────
            elif path == "/api/vaults":
                return current_app.ensure_sync(app_mod.vaults)()
            elif path.startswith("/api/vaults/") and "/query" in path:
                if path.startswith("/api/vaults/__all__/query"):
                    return current_app.ensure_sync(app_mod.vault_all_query)()
                else:
                    name = path.split("/")[3]
                    return current_app.ensure_sync(app_mod.vault_query)(name)
            elif path.startswith("/api/vaults/"):
                name = path.split("/")[-1]
                return current_app.ensure_sync(app_mod.vault_detail)(name)

            # ── Macros ─────────────────────────────────────────────
            elif path == "/api/macros":
                return current_app.ensure_sync(app_mod.macros)()
            elif path.startswith("/api/macros/"):
                if path.endswith("/run"):
                    name = path.split("/")[3]
                    return current_app.ensure_sync(app_mod.macro_run)(name)
                else:
                    name = path.split("/")[-1]
                    return current_app.ensure_sync(app_mod.macro_detail)(name)

            # ── Notifications ──────────────────────────────────────
            elif path == "/api/notifications":
                return current_app.ensure_sync(app_mod.notifications)()
            elif path == "/api/confirm":
                return current_app.ensure_sync(app_mod.confirm)()

            # ── Chat History ──────────────────────────────────────
            elif path == "/api/chats":
                return current_app.ensure_sync(app_mod.chats)()
            elif path.startswith("/api/chats/"):
                cid = path.split("/")[-1]
                return current_app.ensure_sync(app_mod.chat_detail)(cid)

            # ── Transcribe ────────────────────────────────────────
            elif path == "/api/transcribe":
                return current_app.ensure_sync(app_mod.transcribe)()

            else:
                return jsonify({"ok": False, "error": "No handler for this endpoint"}), 404

        # ── v6 AI endpoints ───────────────────────────────────
        def _core_call(method, *args, **kwargs):
            c = core()
            if c is None:
                return {"ok": False, "error": "Core not ready"}
            fn = getattr(c, method, None)
            if fn is None:
                return {"ok": False, "error": f"No method: {method}"}
            print(f"[DEBUG] _core_call calling {method} with args={args}, kwargs={kwargs}")
            try:
                return fn(*args, **kwargs)
            except Exception as e:
                return {"ok": False, "error": str(e)}

        @app.route("/api/v6/app/open", methods=["POST"])
        def v6_open():
            d = request.get_json(force=True)
            app_name = d.get("app", "")
            print(f"[DEBUG] v6_open called with app: {app_name}")
            print(f"[DEBUG] iface: {iface}")
            print(f"[DEBUG] iface.core: {iface.core}")
            c = iface.core
            if c is None:
                return jsonify({"ok": False, "error": "Core not ready"})
            result = c.open_app(app_name)
            print(f"[DEBUG] open_app result: {result}")
            return jsonify(result)

        @app.route("/api/v6/app/list", methods=["POST"])
        def v6_list():
            return jsonify(_core_call("list_apps"))

        @app.route("/api/v6/phone/status", methods=["POST"])
        def v6_ps():
            c = core()
            return jsonify(c.phone.get_status() if c and c.phone else {"ok": True, "device_connected": False})

        @app.route("/api/v6/phone/sms/send", methods=["POST"])
        def v6_sms_send():
            d = request.get_json(force=True)
            return jsonify(_core_call("send_sms", d.get("phone_number", ""), d.get("message", "")))

        @app.route("/api/v6/phone/sms/read", methods=["POST"])
        def v6_sms_read():
            d = request.get_json(force=True)
            return jsonify(_core_call("read_sms", int(d.get("limit", 10))))

        @app.route("/api/v6/phone/whatsapp/send", methods=["POST"])
        def v6_wa():
            d = request.get_json(force=True)
            return jsonify(_core_call("send_whatsapp", d.get("phone_number", ""), d.get("message", "")))

        @app.route("/api/v6/voice/hotword", methods=["POST"])
        def v6_hotword():
            return jsonify(_core_call("start_hotword"))

        @app.route("/api/v6/biometric/register", methods=["POST"])
        def v6_reg():
            d = request.get_json(force=True)
            return jsonify(_core_call("register_user", d.get("user_id", ""), d.get("methods")))

        @app.route("/api/v6/biometric/authenticate", methods=["POST"])
        def v6_auth():
            d = request.get_json(force=True)
            return jsonify(_core_call("authenticate", d.get("method", "any")))

        @app.route("/api/v6/biometric/status", methods=["POST"])
        def v6_bst():
            return jsonify(_core_call("get_biometric_status"))

        @app.route("/api/v6/smart/emotion", methods=["POST"])
        def v6_emo():
            d = request.get_json(force=True)
            return jsonify(_core_call("detect_emotion", d.get("text", "")))

        @app.route("/api/v6/smart/suggest", methods=["POST"])
        def v6_sugg():
            d = request.get_json(force=True)
            return jsonify(_core_call("get_suggestions", d.get("context", "")))

        @app.route("/api/v6/smart/history", methods=["POST"])
        def v6_hist():
            d = request.get_json(force=True)
            return jsonify(_core_call("search_history", d.get("query", ""), int(d.get("limit", 20))))

        @app.route("/api/v6/smart/analytics", methods=["POST"])
        def v6_anal():
            return jsonify(_core_call("get_analytics"))

        # ── Gmail endpoints ───────────────────────────────────
        def _gmail(method, *args, **kwargs):
            try:
                from gmail_integration import GmailClient
                g = GmailClient()
                return getattr(g, method)(*args, **kwargs)
            except Exception as e:
                return {"ok": False, "error": str(e)}

        @app.route("/api/v6/gmail/connect", methods=["POST"])
        def gmail_connect():
            try:
                from gmail_integration import GmailClient
                g = GmailClient()
                p = g.get_profile()
                return jsonify({"ok": True, "message": f"Connected as {p.get('email', '?')}"})
            except Exception as e:
                return jsonify({"ok": False, "error": str(e)})

        @app.route("/api/v6/gmail/list", methods=["POST"])
        def gmail_list():
            d = request.get_json(force=True)
            return jsonify(_gmail("list_emails", d.get("max_results", 15), d.get("label", "INBOX"), d.get("query", "")))

        @app.route("/api/v6/gmail/search", methods=["POST"])
        def gmail_search():
            d = request.get_json(force=True)
            return jsonify(_gmail("search_emails", d.get("query", ""), d.get("max_results", 15)))

        @app.route("/api/v6/gmail/get", methods=["POST"])
        def gmail_get():
            d = request.get_json(force=True)
            return jsonify(_gmail("get_email", d.get("email_id", "")))

        @app.route("/api/v6/gmail/send", methods=["POST"])
        def gmail_send():
            d = request.get_json(force=True)
            return jsonify(_gmail("send_email", d.get("to", ""), d.get("subject", ""), d.get("body", ""),
                                  cc=d.get("cc", ""), bcc=d.get("bcc", "")))

        @app.route("/api/v6/gmail/reply", methods=["POST"])
        def gmail_reply():
            d = request.get_json(force=True)
            return jsonify(_gmail("reply_email", d.get("email_id", ""), d.get("body", "")))

        @app.route("/api/v6/gmail/mark_read", methods=["POST"])
        def gmail_mark():
            d = request.get_json(force=True)
            return jsonify(_gmail("mark_as_read", d.get("email_id", "")))

        @app.route("/api/v6/gmail/trash", methods=["POST"])
        def gmail_trash():
            d = request.get_json(force=True)
            return jsonify(_gmail("trash_email", d.get("email_id", "")))

        @app.route("/api/v6/gmail/profile", methods=["POST"])
        def gmail_profile():
            return jsonify(_gmail("get_profile"))

        # ── WebSocket ─────────────────────────────────────────
        @sio.on("connect")
        def on_connect(): emit("log_event",{"text":"UI connected","cls":"ok"})

        def _push_stats():
            while True:
                try:
                    c = core()
                    if c:
                        s = c.get_stats()
                        sio.emit("stats_update", s.get("info") or s)
                except Exception:
                    pass
                time.sleep(8)

        threading.Thread(target=_push_stats, daemon=True).start()

    # ── Start ─────────────────────────────────────────────────

    def start(self):
        print(f"  Web UI → http://{self.host}:{self.port}")
        self.sio.run(self.app, host=self.host, port=self.port,
                     debug=False, use_reloader=False, log_output=False)

    def start_threaded(self):
        t = threading.Thread(target=self.start, daemon=True)
        t.start()
        return t
