# brain.py
# Shadow Bot – Brain Module v2.0
# Insight engine: streak detection, mood analysis,
# saran taktis dinamis, export otomatis
#
# Dipanggil langsung: python brain.py
# Atau dari orchestrator: modules.brain.run()

import os
import datetime

# ── Import modules ────────────────────────────────────────
from modules.analyzer import (
    analisa_mingguan,
    analisa_mood,
    analisa_streak,
    analisa_jam_aktif,
    analisa_topik,
    generate_saran,
)
from modules.memory_manager import (
    load_short,
    load_long,
    memory_stats,
    sync_from_main,
    update_streak,
    promote_to_long,
)

# ── Config ────────────────────────────────────────────────
INSIGHT_LOG_DIR  = "logs"
INSIGHT_LOG_FILE = os.path.join(INSIGHT_LOG_DIR, "brain_insights.log")
EXPORT_DIR       = "exports"

# ====================================================
# A. CORE INSIGHT GENERATOR
# ====================================================

def generate_insight(mode="full"):
    """
    Generate insight dari semua sumber data.
    mode: 'full' | 'short' | 'streak' | 'mood'
    Return: string insight siap print/export
    """
    # Sync dulu biar data fresh
    sync_from_main()
    update_streak()
    if memory_stats().get("short_full"):
        promote_to_long()

    # Kumpulkan semua data
    stats   = memory_stats()
    mood    = analisa_mood(days=7)
    streak  = analisa_streak()
    jam     = analisa_jam_aktif()
    weekly  = analisa_mingguan()
    saran   = generate_saran(stats, mood, streak, jam)

    now_str = datetime.datetime.now().strftime("%d %b %Y, %H:%M")

    lines = []

    # ── Header ────────────────────────────────────────────
    lines.append("=" * 50)
    lines.append("  SHADOW BRAIN INSIGHT v2.0")
    lines.append(f"  {now_str}")
    lines.append("=" * 50)

    if mode in ("full", "short"):
        # ── Memory summary ────────────────────────────────
        lines.append("")
        lines.append("[ MEMORY ]")
        lines.append(f"  Total interaksi   : {stats['total']}")
        lines.append(f"  - Short-term      : {stats['short_count']}")
        lines.append(f"  - Long-term       : {stats['long_count']}")
        if stats['short_count'] > 0:
            last_time = _get_last_time()
            if last_time:
                lines.append(f"  Terakhir aktif    : {last_time}")

    if mode in ("full", "streak"):
        # ── Streak ────────────────────────────────────────
        lines.append("")
        lines.append("[ STREAK ]")
        lines.append(f"  Streak saat ini   : {streak['current']} hari")
        lines.append(f"  Streak terbaik    : {streak['best']} hari")
        lines.append(f"  Status            : {streak['status'].upper()}")
        if streak["last_date"]:
            lines.append(f"  Terakhir aktif    : {streak['last_date']}")
        if streak["gap_days"] > 0:
            lines.append(f"  Gap tidak aktif   : {streak['gap_days']} hari")
        if streak["warning"]:
            lines.append(f"  ⚠ WARNING: {streak['warning']}")

    if mode in ("full", "mood"):
        # ── Mood analysis ──────────────────────────────────
        lines.append("")
        lines.append("[ MOOD (7 hari terakhir) ]")
        dist = mood["distribution"]
        if dist:
            for m, count in sorted(dist.items(), key=lambda x: -x[1]):
                bar = "▪" * min(count, 20)
                lines.append(f"  {m.ljust(10)} {bar} ({count}x)")
        else:
            lines.append("  Belum ada data mood.")
        lines.append(f"  Dominant          : {mood['dominant'] or '-'}")
        lines.append(f"  Trend             : {mood['trend']}")

    if mode == "full":
        # ── Jam aktif ─────────────────────────────────────
        lines.append("")
        lines.append("[ JAM AKTIF ]")
        if jam["peak_hour"] is not None:
            lines.append(f"  Peak jam          : {jam['peak_hour']:02d}.00 ({jam['label']})")
            # Mini bar chart jam
            dist_jam = jam.get("distribution", {})
            if dist_jam:
                max_val = max(dist_jam.values()) if dist_jam else 1
                lines.append("  Distribusi per jam:")
                for h in sorted(dist_jam.keys()):
                    count   = dist_jam[h]
                    bar_len = int((count / max_val) * 15)
                    bar     = "█" * bar_len + "░" * (15 - bar_len)
                    lines.append(f"    {h:02d}:00  {bar} {count}")
        else:
            lines.append("  Belum ada data aktivitas.")

        # ── Topik ─────────────────────────────────────────
        lines.append("")
        lines.append("[ TOPIK TERBANYAK ]")
        top_topics = analisa_topik(top_n=5)
        if top_topics:
            for topic, count in top_topics:
                bar = "▪" * min(count, 20)
                lines.append(f"  {topic.ljust(14)} {bar} ({count}x)")
        else:
            lines.append("  Belum ada data topik.")

        # ── Weekly ────────────────────────────────────────
        lines.append("")
        lines.append("[ RINGKASAN MINGGUAN ]")
        for l in weekly.splitlines():
            lines.append(f"  {l}")

    # ── Saran ─────────────────────────────────────────────
    lines.append("")
    lines.append("[ SARAN TAKTIS ]")
    for s in saran:
        lines.append(f"  → {s}")

    lines.append("")
    lines.append("=" * 50)

    return "\n".join(lines)

# ====================================================
# B. EXPORT INSIGHT
# ====================================================

def export_insight(content, fmt="txt"):
    """
    Export insight ke file.
    fmt: 'txt' | 'log'
    Return path file yang dibuat.
    """
    os.makedirs(EXPORT_DIR, exist_ok=True)
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")

    if fmt == "txt":
        path = os.path.join(EXPORT_DIR, f"insight_{timestamp}.txt")
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
    elif fmt == "log":
        path = INSIGHT_LOG_FILE
        os.makedirs(INSIGHT_LOG_DIR, exist_ok=True)
        with open(path, "a", encoding="utf-8") as f:
            f.write(content + "\n\n")
    else:
        raise ValueError(f"Format tidak dikenal: {fmt}")

    return path

# ====================================================
# C. AUTO-LOG (dipanggil dari orchestrator/scheduler)
# ====================================================

def auto_log_insight():
    """
    Generate insight 'short' dan append ke brain_insights.log.
    Cocok dipanggil dari scheduler/orchestrator tiap hari.
    """
    content = generate_insight(mode="short")
    path    = export_insight(content, fmt="log")
    print(f"[Brain] Auto-log saved → {path}")
    return path

# ====================================================
# D. STREAK-ONLY REPORT
# ====================================================

def streak_report():
    """
    Quick report hanya fokus ke streak + warning.
    Dipanggil dari triggers.py atau watchdog.
    """
    update_streak()
    streak = analisa_streak()
    lines  = ["[ STREAK REPORT ]"]
    lines.append(f"  Streak : {streak['current']} hari (terbaik: {streak['best']})")
    lines.append(f"  Status : {streak['status'].upper()}")
    if streak["warning"]:
        lines.append(f"  ⚠ {streak['warning']}")
    return "\n".join(lines)

# ====================================================
# E. MOOD-ONLY REPORT
# ====================================================

def mood_report(days=7):
    """Quick report fokus mood. Bisa dipanggil dari triggers.py."""
    mood  = analisa_mood(days=days)
    lines = [f"[ MOOD REPORT ({days} hari terakhir) ]"]
    dist  = mood["distribution"]
    if dist:
        for m, count in sorted(dist.items(), key=lambda x: -x[1]):
            lines.append(f"  {m.ljust(10)}: {count}x")
    else:
        lines.append("  Belum ada data mood.")
    lines.append(f"  Dominant : {mood['dominant'] or '-'}")
    lines.append(f"  Trend    : {mood['trend']}")
    return "\n".join(lines)

# ====================================================
# F. UTIL
# ====================================================

def _get_last_time():
    """Ambil timestamp entry terakhir dari short_term."""
    short = load_short()
    h     = short.get("history", [])
    if h:
        raw = h[-1].get("time","")
        try:
            dt = datetime.datetime.fromisoformat(raw)
            return dt.strftime("%d %b %Y, %H:%M")
        except Exception:
            return raw
    return None

# ====================================================
# G. RUN (entry point)
# ====================================================

def run(mode="full", export=False):
    """
    Entry point utama.
    mode   : 'full' | 'short' | 'streak' | 'mood'
    export : True → simpan ke file TXT sekaligus
    """
    insight = generate_insight(mode=mode)
    print(insight)

    # Auto-append ke log setiap kali run
    export_insight(insight, fmt="log")

    # Export ke TXT kalau diminta
    if export:
        path = export_insight(insight, fmt="txt")
        print(f"\n[Brain] Insight diekspor → {path}")

    return insight

# ====================================================
# H. CLI LANGSUNG
# ====================================================

if __name__ == "__main__":
    import sys

    args   = sys.argv[1:]
    mode   = "full"
    export = False

    if "--short" in args:   mode = "short"
    if "--streak" in args:  mode = "streak"
    if "--mood" in args:    mode = "mood"
    if "--export" in args:  export = True

    if "--help" in args:
        print("Usage: python brain.py [--short|--streak|--mood] [--export]")
        print("  --short   Insight ringkas (memory + streak)")
        print("  --streak  Hanya laporan streak")
        print("  --mood    Hanya laporan mood")
        print("  --export  Simpan insight ke file TXT di exports/")
        sys.exit(0)

    run(mode=mode, export=export)
