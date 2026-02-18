# core/analyzer.py
# AKARU – Local Analyzer
# Pola kebiasaan & skor produktivitas — pure JSON math, zero ML

from datetime import datetime, timedelta
from collections import Counter
from core.config import LOG_FILE, MOOD_FILE, load_json
from core import display as D

def _load_logs():
    return load_json(LOG_FILE, [])

def _load_mood():
    return load_json(MOOD_FILE, [])

def _parse_date(iso):
    try:
        return datetime.fromisoformat(iso).strftime("%Y-%m-%d")
    except Exception:
        return None

# ── Produktivitas Score ───────────────────────────────────
def productivity_score(memory):
    """
    Skor 0-100 berdasarkan:
    - Rasio tugas selesai       (40 poin)
    - Catatan aktif minggu ini  (30 poin)
    - Streak hari aktif (log)   (30 poin)
    """
    tasks  = memory.get("tasks", [])
    notes  = memory.get("notes", [])
    logs   = _load_logs()

    # 1. Task completion ratio
    total = len(tasks)
    done  = len([t for t in tasks if t.get("done")])
    task_score = int((done / total) * 40) if total > 0 else 0

    # 2. Notes this week
    week_ago = (datetime.now() - timedelta(days=7)).isoformat()
    recent_notes = [n for n in notes if n.get("t", "") >= week_ago]
    note_score = min(len(recent_notes) * 6, 30)  # cap 30

    # 3. Active days streak (from logs, last 14 days)
    active_days = set()
    for entry in logs:
        d = _parse_date(entry.get("t", ""))
        if d:
            active_days.add(d)
    today = datetime.now().strftime("%Y-%m-%d")
    streak = 0
    for i in range(14):
        day = (datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d")
        if day in active_days:
            streak += 1
        else:
            break
    streak_score = min(streak * 3, 30)  # cap 30

    total_score = task_score + note_score + streak_score
    return {
        "score"        : total_score,
        "task_score"   : task_score,
        "note_score"   : note_score,
        "streak_score" : streak_score,
        "streak_days"  : streak,
        "done_tasks"   : done,
        "total_tasks"  : total,
        "notes_week"   : len(recent_notes),
    }

# ── Pola Aktivitas ────────────────────────────────────────
def activity_pattern():
    """Jam paling aktif berdasarkan log."""
    logs = _load_logs()
    if not logs:
        return None
    hours = []
    for entry in logs:
        try:
            h = datetime.fromisoformat(entry["t"]).hour
            hours.append(h)
        except Exception:
            pass
    if not hours:
        return None
    counter = Counter(hours)
    peak_hour = counter.most_common(1)[0][0]
    return {
        "peak_hour" : peak_hour,
        "peak_label": _hour_label(peak_hour),
        "distribution": dict(sorted(counter.items())),
    }

def _hour_label(h):
    if 5  <= h < 9:  return "Pagi"
    if 9  <= h < 12: return "Pagi menjelang siang"
    if 12 <= h < 15: return "Siang"
    if 15 <= h < 18: return "Sore"
    if 18 <= h < 21: return "Malam"
    return "Larut malam"

# ── Intent Distribution ───────────────────────────────────
def intent_distribution():
    logs = _load_logs()
    intents = [e.get("i", "?") for e in logs]
    return dict(Counter(intents).most_common(8))

# ── Mood Correlation ──────────────────────────────────────
def mood_vs_productivity():
    """Rata-rata mood pada hari aktif vs tidak aktif."""
    mood_data = _load_mood()
    logs      = _load_logs()
    if not mood_data or not logs:
        return None

    active_dates = set()
    for e in logs:
        d = _parse_date(e.get("t", ""))
        if d:
            active_dates.add(d)

    active_moods   = [e["mood"] for e in mood_data if e.get("date") in active_dates]
    inactive_moods = [e["mood"] for e in mood_data if e.get("date") not in active_dates]

    return {
        "active_avg"  : round(sum(active_moods)   / len(active_moods),   1) if active_moods   else None,
        "inactive_avg": round(sum(inactive_moods) / len(inactive_moods), 1) if inactive_moods else None,
    }

# ── Display Analyzer ─────────────────────────────────────
def show_analysis(memory):
    D.header("ANALISIS PRODUKTIVITAS", D.CYAN)

    ps = productivity_score(memory)
    score = ps["score"]

    # Score bar
    filled = score // 5
    bar = D.c("█" * filled, D.GREEN) + D.c("░" * (20 - filled), D.GRAY)
    label_color = D.GREEN if score >= 70 else (D.YELLOW if score >= 40 else D.RED)

    print(f"  {D.c('Skor', D.GRAY)}  {bar}  {D.c(f'{score}/100', label_color, D.BOLD)}")
    D.blank()
    D.info("Task selesai",   f"{ps['done_tasks']}/{ps['total_tasks']} ({ps['task_score']} poin)")
    D.info("Catatan minggu ini", f"{ps['notes_week']} catatan ({ps['note_score']} poin)")
    D.info("Streak aktif",   f"{ps['streak_days']} hari ({ps['streak_score']} poin)")

    # Pola jam
    pattern = activity_pattern()
    if pattern:
        D.blank()
        D.info("Paling aktif",  f"Jam {pattern['peak_hour']:02d}.00 ({pattern['peak_label']})")

    # Intent terbanyak
    dist = intent_distribution()
    if dist:
        D.blank()
        print(f"  {D.c('Aktivitas terbanyak:', D.GRAY)}")
        for intent, count in list(dist.items())[:4]:
            bar_w = min(count, 20)
            bar_s = D.c("▪" * bar_w, D.CYAN)
            print(f"    {intent.ljust(16)} {bar_s} {D.c(count, D.GRAY)}")

    # Mood vs produktivitas
    corr = mood_vs_productivity()
    if corr and corr["active_avg"] and corr["inactive_avg"]:
        D.blank()
        D.info("Mood saat aktif",    f"{corr['active_avg']} / 5")
        D.info("Mood saat tidak aktif", f"{corr['inactive_avg']} / 5")

    D.sep()
