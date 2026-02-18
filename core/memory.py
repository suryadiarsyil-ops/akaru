# core/memory.py
# AKARU – Memory Layer
# Cold memory  = catatan & tugas (persisten ke disk)
# Context      = sesi terakhir (siapa, apa, kapan terakhir aktif)

from datetime import datetime
from core.config import (
    MEMORY_FILE, CONTEXT_FILE, LOG_FILE,
    load_json, save_json,
)

# ── Schema default ────────────────────────────────────────
def _default_memory():
    return {"notes": [], "tasks": []}

def _default_context():
    return {
        "last_active"   : None,
        "last_intent"   : None,
        "last_note"     : None,
        "session_count" : 0,
        "streak_days"   : 0,
        "last_date"     : None,
    }

# ── Load ──────────────────────────────────────────────────
def load_memory():
    m = load_json(MEMORY_FILE, _default_memory)
    m.setdefault("notes", [])
    m.setdefault("tasks", [])
    return m

def load_context():
    ctx = load_json(CONTEXT_FILE, _default_context)
    for k, v in _default_context().items():
        ctx.setdefault(k, v)
    return ctx

def load_logs():
    return load_json(LOG_FILE, [])

# ── Save ──────────────────────────────────────────────────
def save_memory(m):
    save_json(MEMORY_FILE, m)

def save_context(ctx):
    save_json(CONTEXT_FILE, ctx)

def save_logs(logs):
    save_json(LOG_FILE, logs)

# ── Context update ────────────────────────────────────────
def update_context(ctx, intent, note_text=None):
    today = datetime.now().strftime("%Y-%m-%d")
    ctx["last_active"] = datetime.now().isoformat(timespec="seconds")
    ctx["last_intent"] = intent
    if note_text:
        ctx["last_note"] = note_text[:80]

    # streak
    last = ctx.get("last_date")
    if last != today:
        from datetime import timedelta
        yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
        if last == yesterday:
            ctx["streak_days"] = ctx.get("streak_days", 0) + 1
        else:
            ctx["streak_days"] = 1
        ctx["last_date"] = today

    save_context(ctx)

def start_session(ctx):
    ctx["session_count"] = ctx.get("session_count", 0) + 1
    save_context(ctx)

# ── Note helpers ──────────────────────────────────────────
def add_note(memory, text):
    nid = (memory["notes"][-1]["id"] + 1) if memory["notes"] else 1
    note = {"id": nid, "t": _now(), "v": text}
    memory["notes"].append(note)
    save_memory(memory)
    return note

def delete_note(memory, nid):
    before = len(memory["notes"])
    memory["notes"] = [n for n in memory["notes"] if n["id"] != nid]
    if len(memory["notes"]) < before:
        save_memory(memory)
        return True
    return False

# ── Task helpers ──────────────────────────────────────────
def add_task(memory, text):
    tid = (memory["tasks"][-1]["id"] + 1) if memory["tasks"] else 1
    task = {"id": tid, "t": _now(), "v": text, "done": False}
    memory["tasks"].append(task)
    save_memory(memory)
    return task

def complete_task(memory, tid):
    for tk in memory["tasks"]:
        if tk["id"] == tid:
            tk["done"] = True
            tk["done_at"] = _now()
            save_memory(memory)
            return tk
    return None

def delete_task(memory, tid):
    before = len(memory["tasks"])
    memory["tasks"] = [t for t in memory["tasks"] if t["id"] != tid]
    if len(memory["tasks"]) < before:
        save_memory(memory)
        return True
    return False

# ── Log helpers ───────────────────────────────────────────
def append_log(logs, intent, ok=True, note="", max_logs=80):
    entry = {"t": _now(), "i": intent, "ok": ok}
    if note:
        entry["n"] = note
    logs.append(entry)
    if len(logs) > max_logs:
        logs[:] = logs[-(max_logs // 2):]
    save_logs(logs)

# ── Util ──────────────────────────────────────────────────
def _now():
    return datetime.now().isoformat(timespec="seconds")
