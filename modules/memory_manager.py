# modules/memory_manager.py
# Shadow Bot – Memory Manager
# Mengelola short_term (sesi aktif) dan long_term (pola persisten)
# Kompatibel dengan memory.json dari akaru_bot.py

import os
import json
import datetime

# ── Path ──────────────────────────────────────────────────
MEMORY_DIR       = "memory"
SHORT_TERM_FILE  = os.path.join(MEMORY_DIR, "short_term.json")
LONG_TERM_FILE   = os.path.join(MEMORY_DIR, "long_term.json")
MAIN_MEMORY_FILE = "memory.json"  # dari akaru_bot.py

# ── Batas ─────────────────────────────────────────────────
SHORT_TERM_MAX   = 30   # entry maksimal di short_term sebelum promote
LONG_TERM_MAX    = 200  # entry maksimal di long_term sebelum trim

# ── Util ──────────────────────────────────────────────────
def _ensure_dir():
    os.makedirs(MEMORY_DIR, exist_ok=True)

def _load(path, default):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return default() if callable(default) else default

def _save(path, data):
    _ensure_dir()
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def _now():
    return datetime.datetime.now().isoformat(timespec="seconds")

def _today():
    return datetime.datetime.now().strftime("%Y-%m-%d")

# ── Schema default ─────────────────────────────────────────
def _default_short():
    return {
        "created": _now(),
        "history": []
    }

def _default_long():
    return {
        "created": _now(),
        "history": [],
        "mood_log": [],
        "topic_freq": {},
        "streak": {
            "current": 0,
            "last_date": None,
            "best": 0
        }
    }

# ── Load ──────────────────────────────────────────────────
def load_short():
    """Load short-term memory (sesi berjalan / data fresh)."""
    data = _load(SHORT_TERM_FILE, _default_short)
    data.setdefault("history", [])
    return data

def load_long():
    """Load long-term memory (pola & riwayat panjang)."""
    data = _load(LONG_TERM_FILE, _default_long)
    data.setdefault("history", [])
    data.setdefault("mood_log", [])
    data.setdefault("topic_freq", {})
    data.setdefault("streak", {"current": 0, "last_date": None, "best": 0})
    return data

def load_main():
    """Load memory.json dari akaru_bot.py (bridge)."""
    return _load(MAIN_MEMORY_FILE, {"history": [], "nama": "User"})

# ── Save ──────────────────────────────────────────────────
def save_short(data):
    _save(SHORT_TERM_FILE, data)

def save_long(data):
    _save(LONG_TERM_FILE, data)

# ── Sync dari akaru_bot.py ────────────────────────────────
def sync_from_main():
    """
    Tarik entry baru dari memory.json ke short_term.
    Dipanggil saat bot startup atau manual sync.
    """
    main    = load_main()
    short   = load_short()
    main_h  = main.get("history", [])
    short_h = short.get("history", [])

    # Ambil entry yang belum ada di short (pakai 'time' sebagai ID unik)
    existing_times = {e.get("time") for e in short_h}
    new_entries = [e for e in main_h if e.get("time") not in existing_times]

    if new_entries:
        short["history"].extend(new_entries)
        save_short(short)
        print(f"[MemoryManager] Sync: {len(new_entries)} entry baru dari memory.json")
    else:
        print("[MemoryManager] Sync: tidak ada entry baru.")

    return len(new_entries)

# ── Promote short → long ──────────────────────────────────
def promote_to_long():
    """
    Pindahkan short_term ke long_term jika sudah penuh.
    Hitung frekuensi topik & mood log sebelum promote.
    """
    short = load_short()
    long  = load_long()

    history = short.get("history", [])
    if len(history) < SHORT_TERM_MAX:
        return False  # belum waktunya promote

    print(f"[MemoryManager] Promoting {len(history)} entry ke long_term...")

    # Hitung frekuensi topik
    topic_freq = long.get("topic_freq", {})
    for entry in history:
        for topic in entry.get("tags", {}).get("topics", []):
            topic_freq[topic] = topic_freq.get(topic, 0) + 1

    # Log mood
    mood_log = long.get("mood_log", [])
    for entry in history:
        mood = entry.get("tags", {}).get("mood")
        if mood:
            mood_log.append({
                "time" : entry.get("time", _now()),
                "mood" : mood
            })

    # Tambahkan ke long_term history (trim kalau terlalu panjang)
    long["history"].extend(history)
    if len(long["history"]) > LONG_TERM_MAX:
        long["history"] = long["history"][-LONG_TERM_MAX:]

    long["topic_freq"] = topic_freq
    long["mood_log"]   = mood_log[-500:]  # cap 500 mood entries
    save_long(long)

    # Reset short_term
    short["history"] = []
    save_short(short)

    print("[MemoryManager] Promote selesai.")
    return True

# ── Streak tracker ────────────────────────────────────────
def update_streak():
    """Update streak hari aktif berdasarkan last entry di short_term."""
    short   = load_short()
    long    = load_long()
    streak  = long.get("streak", {"current": 0, "last_date": None, "best": 0})
    history = short.get("history", [])

    if not history:
        return streak

    last_entry_time = history[-1].get("time", "")
    try:
        last_date = last_entry_time[:10]  # ambil YYYY-MM-DD
    except Exception:
        return streak

    today     = _today()
    yesterday = (datetime.datetime.now() - datetime.timedelta(days=1)).strftime("%Y-%m-%d")

    if last_date == today:
        if streak["last_date"] == yesterday:
            streak["current"] += 1
        elif streak["last_date"] != today:
            streak["current"] = 1
        streak["last_date"] = today
        streak["best"] = max(streak["best"], streak["current"])
        long["streak"] = streak
        save_long(long)

    return streak

# ── Statistik ringkas ─────────────────────────────────────
def memory_stats():
    """Return dict ringkasan kondisi memory untuk brain.py / watchdog."""
    short = load_short()
    long  = load_long()
    return {
        "short_count"  : len(short.get("history", [])),
        "long_count"   : len(long.get("history", [])),
        "total"        : len(short.get("history", [])) + len(long.get("history", [])),
        "topic_freq"   : long.get("topic_freq", {}),
        "mood_log_len" : len(long.get("mood_log", [])),
        "streak"       : long.get("streak", {}),
        "short_full"   : len(short.get("history", [])) >= SHORT_TERM_MAX,
    }

# ── Flush / trim manual ───────────────────────────────────
def flush_old_long(keep_last=100):
    """Trim long_term, simpan hanya `keep_last` entry terbaru."""
    long = load_long()
    before = len(long["history"])
    long["history"] = long["history"][-keep_last:]
    save_long(long)
    removed = before - len(long["history"])
    print(f"[MemoryManager] Flush: {removed} entry lama dihapus dari long_term.")
    return removed

# ── Entry point (run dari orchestrator) ──────────────────
def run():
    print("[MemoryManager] Sync & check...")
    synced = sync_from_main()
    stats  = memory_stats()
    print(f"  Short: {stats['short_count']} | Long: {stats['long_count']} | Total: {stats['total']}")
    print(f"  Streak: {stats['streak'].get('current', 0)} hari")

    if stats["short_full"]:
        print("  [!] Short-term penuh, promote ke long-term...")
        promote_to_long()

    update_streak()
    print("[MemoryManager] Done.")
