# core/mood.py
# AKARU – Mood & Energy Tracker
# Pure manual input, zero library eksternal

from datetime import datetime
from core.config import MOOD_FILE, load_json, save_json
from core import display as D

# ── Schema ────────────────────────────────────────────────
MOOD_LABELS = {
    "1": ("💀", "Hancur",     D.RED),
    "2": ("😓", "Berat",      D.MAGENTA),
    "3": ("😐", "Biasa",      D.GRAY),
    "4": ("😊", "Oke",        D.YELLOW),
    "5": ("🔥", "Semangat",   D.GREEN),
}

ENERGY_LABELS = {
    "1": ("🪫", "Kosong",     D.RED),
    "2": ("🔋", "Rendah",     D.MAGENTA),
    "3": ("⚡", "Sedang",     D.YELLOW),
    "4": ("💪", "Tinggi",     D.GREEN),
    "5": ("🚀", "Full gas",   D.CYAN),
}

def _now():
    return datetime.now().isoformat(timespec="seconds")

def _today():
    return datetime.now().strftime("%Y-%m-%d")

def _load():
    return load_json(MOOD_FILE, [])

def _save(data):
    save_json(MOOD_FILE, data)

# ── Input mood ────────────────────────────────────────────
def prompt_mood():
    """Interaktif input mood + energy. Return dict entry atau None."""
    D.header("MOOD & ENERGY CHECK-IN", D.MAGENTA)
    print(D.c("  Mood sekarang (1-5):", D.WHITE))
    for k, (ico, label, col) in MOOD_LABELS.items():
        print(f"    {D.c(k, col, D.BOLD)}  {ico}  {D.c(label, col)}")
    D.blank()

    mood_raw = input(D.c("  Pilih mood [1-5]: ", D.CYAN)).strip()
    if mood_raw not in MOOD_LABELS:
        D.err("Input tidak valid, mood check-in dibatalkan.")
        return None

    D.blank()
    print(D.c("  Energi sekarang (1-5):", D.WHITE))
    for k, (ico, label, col) in ENERGY_LABELS.items():
        print(f"    {D.c(k, col, D.BOLD)}  {ico}  {D.c(label, col)}")
    D.blank()

    energy_raw = input(D.c("  Pilih energi [1-5]: ", D.CYAN)).strip()
    if energy_raw not in ENERGY_LABELS:
        D.err("Input tidak valid, mood check-in dibatalkan.")
        return None

    note_raw = input(D.c("  Catatan singkat (opsional, Enter skip): ", D.GRAY)).strip()

    entry = {
        "t"      : _now(),
        "date"   : _today(),
        "mood"   : int(mood_raw),
        "energy" : int(energy_raw),
        "note"   : note_raw or "",
    }

    data = _load()
    data.append(entry)
    _save(data)

    m_ico, m_lbl, m_col = MOOD_LABELS[mood_raw]
    e_ico, e_lbl, e_col = ENERGY_LABELS[energy_raw]
    D.blank()
    D.ok(f"Mood {m_ico} {D.c(m_lbl, m_col)}  ·  Energi {e_ico} {D.c(e_lbl, e_col)} — disimpan.")
    return entry

# ── View riwayat ──────────────────────────────────────────
def view_mood(n=7):
    data = _load()
    if not data:
        D.dim("Belum ada data mood.")
        return

    recent = data[-n:]
    D.header(f"MOOD LOG ({len(recent)} terakhir)", D.MAGENTA)
    for e in recent:
        mood_ico  = MOOD_LABELS.get(str(e["mood"]),  ("?", "?", D.GRAY))[0]
        energy_ico= ENERGY_LABELS.get(str(e["energy"]),("?","?",D.GRAY))[0]
        note_str  = D.c('  "' + e['note'] + '"', D.DIM) if e.get("note") else ""
        date_str  = D.c(e["date"], D.GRAY)
        print(f"  {date_str}  Mood {mood_ico} {e['mood']}  Energi {energy_ico} {e['energy']}{note_str}")
    D.sep()

# ── Stats ringkas ─────────────────────────────────────────
def mood_stats():
    data = _load()
    if not data:
        return None
    recent = data[-30:]  # 30 entry terakhir
    avg_mood   = sum(e["mood"]   for e in recent) / len(recent)
    avg_energy = sum(e["energy"] for e in recent) / len(recent)
    return {
        "count"      : len(recent),
        "avg_mood"   : round(avg_mood, 1),
        "avg_energy" : round(avg_energy, 1),
        "last_mood"  : recent[-1]["mood"],
        "last_energy": recent[-1]["energy"],
    }
