# core/summary.py
# AKARU – Summary Generator
# Harian & mingguan — generate dari data lokal, pure logic

from datetime import datetime, timedelta
from core.config import load_json, MOOD_FILE
from core import display as D

def _today():
    return datetime.now().strftime("%Y-%m-%d")

def _n_days_ago(n):
    return (datetime.now() - timedelta(days=n)).strftime("%Y-%m-%d")

def _date_of(iso):
    try:
        return datetime.fromisoformat(iso).strftime("%Y-%m-%d")
    except Exception:
        return ""

def _time_of(iso):
    try:
        return datetime.fromisoformat(iso).strftime("%H:%M")
    except Exception:
        return ""

# ── Daily Summary ─────────────────────────────────────────
def daily_summary(memory, context, target_date=None):
    today = target_date or _today()

    notes  = [n for n in memory.get("notes", []) if _date_of(n.get("t","")) == today]
    tasks  = memory.get("tasks", [])
    done_today  = [t for t in tasks if t.get("done") and _date_of(t.get("done_at","")) == today]
    added_today = [t for t in tasks if _date_of(t.get("t","")) == today]
    pending     = [t for t in tasks if not t.get("done")]

    mood_data = load_json(MOOD_FILE, [])
    mood_today = [e for e in mood_data if e.get("date") == today]

    D.header(f"SUMMARY HARIAN – {today}", D.YELLOW)

    # Mood hari ini
    if mood_today:
        last_m = mood_today[-1]
        from core.mood import MOOD_LABELS, ENERGY_LABELS
        m_ico = MOOD_LABELS.get(str(last_m["mood"]), ("?", "?", D.GRAY))[0]
        e_ico = ENERGY_LABELS.get(str(last_m["energy"]), ("?", "?", D.GRAY))[0]
        print(f"  {D.c('Kondisi hari ini:', D.GRAY)} Mood {m_ico} {last_m['mood']}  Energi {e_ico} {last_m['energy']}")
        if last_m.get("note"):
            print(f"  {D.c('→', D.GRAY)} {D.c(last_m['note'], D.DIM)}")
        D.blank()
    else:
        print(f"  {D.c('Mood:', D.GRAY)} {D.c('Belum check-in hari ini', D.GRAY)}")
        D.blank()

    # Catatan hari ini
    print(f"  {D.c('Catatan hari ini:', D.WHITE, D.BOLD)}  {D.c(f'({len(notes)})', D.GRAY)}")
    if notes:
        for n in notes:
            print(f"  {D.c(_time_of(n['t']), D.GRAY)}  {n['v']}")
    else:
        D.dim("  Tidak ada catatan hari ini.")
    D.blank()

    # Tugas
    print(f"  {D.c('Tugas selesai hari ini:', D.WHITE, D.BOLD)}  {D.c(f'({len(done_today)})', D.GREEN)}")
    if done_today:
        for t in done_today:
            print(f"  {D.c('✓', D.GREEN)}  {t['v']}")
    else:
        D.dim("  Belum ada tugas selesai.")
    D.blank()

    if added_today:
        print(f"  {D.c('Tugas ditambah hari ini:', D.WHITE, D.BOLD)}  {D.c(f'({len(added_today)})', D.CYAN)}")
        for t in added_today:
            print(f"  {D.c('+', D.CYAN)}  {t['v']}")
        D.blank()

    # Pending
    print(f"  {D.c('Tugas belum selesai:', D.WHITE, D.BOLD)}  {D.c(f'({len(pending)})', D.YELLOW)}")
    for t in pending[:5]:  # batasi 5 supaya ringkas
        print(f"  {D.c('·', D.YELLOW)}  {t['v']}")
    if len(pending) > 5:
        print(f"  {D.c(f'  ... dan {len(pending)-5} lainnya', D.GRAY)}")

    # Sesi & streak
    D.blank()
    streak = context.get("streak_days", 0)
    scount = context.get("session_count", 0)
    print(f"  {D.c('Streak aktif:', D.GRAY)} {D.c(f'{streak} hari', D.CYAN, D.BOLD)}  ·  {D.c(f'{scount} sesi total', D.GRAY)}")
    D.sep()

# ── Weekly Summary ────────────────────────────────────────
def weekly_summary(memory, context):
    today    = _today()
    week_ago = _n_days_ago(7)

    notes  = [n for n in memory.get("notes", []) if _date_of(n.get("t","")) >= week_ago]
    tasks  = memory.get("tasks", [])
    done_week   = [t for t in tasks if t.get("done") and _date_of(t.get("done_at","")) >= week_ago]
    added_week  = [t for t in tasks if _date_of(t.get("t","")) >= week_ago]
    pending     = [t for t in tasks if not t.get("done")]

    mood_data  = load_json(MOOD_FILE, [])
    mood_week  = [e for e in mood_data if e.get("date","") >= week_ago]
    avg_mood   = round(sum(e["mood"] for e in mood_week) / len(mood_week), 1) if mood_week else None
    avg_energy = round(sum(e["energy"] for e in mood_week) / len(mood_week), 1) if mood_week else None

    # Hari aktif minggu ini
    from core.config import LOG_FILE
    logs = load_json(LOG_FILE, [])
    active_days = set()
    for e in logs:
        d = _date_of(e.get("t",""))
        if d >= week_ago:
            active_days.add(d)

    D.header(f"SUMMARY MINGGUAN  ({week_ago} → {today})", D.CYAN)

    D.info("Hari aktif",       f"{len(active_days)} / 7 hari")
    D.info("Total catatan",    f"{len(notes)}")
    D.info("Tugas diselesaikan", f"{len(done_week)}")
    D.info("Tugas ditambahkan",  f"{len(added_week)}")
    D.info("Tugas tersisa",    f"{len(pending)}")

    if avg_mood is not None:
        D.blank()
        D.info("Rata-rata mood",   f"{avg_mood} / 5")
        D.info("Rata-rata energi", f"{avg_energy} / 5")

    # Catatan terbanyak per hari
    if notes:
        from collections import Counter
        per_day = Counter(_date_of(n["t"]) for n in notes)
        busiest_day, busiest_count = per_day.most_common(1)[0]
        D.blank()
        D.info("Hari paling produktif", f"{busiest_day}  ({busiest_count} catatan)")

    # Highlight task selesai
    if done_week:
        D.blank()
        print(f"  {D.c('Tugas selesai minggu ini:', D.GREEN, D.BOLD)}")
        for t in done_week[:6]:
            print(f"  {D.c('✓', D.GREEN)}  {t['v'][:50]}")
        if len(done_week) > 6:
            print(f"  {D.c(f'  ... dan {len(done_week)-6} lainnya', D.GRAY)}")

    D.blank()
    streak = context.get("streak_days", 0)
    print(f"  {D.c('Streak saat ini:', D.GRAY)} {D.c(f'{streak} hari', D.CYAN, D.BOLD)}")
    D.sep()
