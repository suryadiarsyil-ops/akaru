# modules/analyzer.py
# Shadow Bot – Local Analyzer
# Analisis pola dari short_term + long_term memory
# Pure logic, zero ML, zero library eksternal

import datetime
from collections import Counter

# ── Import memory_manager ─────────────────────────────────
# Lazy import biar tidak circular kalau dipanggil dari brain.py
def _get_mm():
    from modules import memory_manager as mm
    return mm

# ── Util ──────────────────────────────────────────────────
def _parse_date(iso):
    try:
        return datetime.datetime.fromisoformat(iso).strftime("%Y-%m-%d")
    except Exception:
        return None

def _parse_hour(iso):
    try:
        return datetime.datetime.fromisoformat(iso).hour
    except Exception:
        return None

def _today():
    return datetime.datetime.now().strftime("%Y-%m-%d")

def _n_days_ago(n):
    return (datetime.datetime.now() - datetime.timedelta(days=n)).strftime("%Y-%m-%d")

def _all_history():
    """Gabungkan short + long history untuk analisis menyeluruh."""
    mm = _get_mm()
    short = mm.load_short().get("history", [])
    long  = mm.load_long().get("history", [])
    return short + long

# ====================================================
# A. MOOD ANALYSIS
# ====================================================

def analisa_mood(days=7):
    """
    Return dict:
    - distribution: {positif: N, negatif: N, bingung: N, None: N}
    - trend: 'membaik' | 'memburuk' | 'stabil'
    - dominant: mood terbanyak
    - raw: list entry dengan mood
    """
    mm      = _get_mm()
    long    = mm.load_long()
    cutoff  = _n_days_ago(days)

    mood_log = [
        e for e in long.get("mood_log", [])
        if (e.get("time", "") or "")[:10] >= cutoff
    ]

    # Kalau mood_log kosong, fallback ke history
    if not mood_log:
        all_h = _all_history()
        mood_log = [
            {"time": e.get("time",""), "mood": e.get("tags",{}).get("mood")}
            for e in all_h
            if e.get("tags",{}).get("mood") and (e.get("time",""))[:10] >= cutoff
        ]

    if not mood_log:
        return {
            "distribution": {},
            "trend": "tidak ada data",
            "dominant": None,
            "raw": []
        }

    dist = Counter(e["mood"] for e in mood_log if e.get("mood"))

    # Trend: bandingkan paruh pertama vs paruh kedua
    mid   = len(mood_log) // 2
    first = mood_log[:mid]
    last  = mood_log[mid:]
    score = {"positif": 1, "negatif": -1, "bingung": 0}
    s1 = sum(score.get(e.get("mood",""), 0) for e in first)
    s2 = sum(score.get(e.get("mood",""), 0) for e in last)
    trend = "membaik" if s2 > s1 else ("memburuk" if s2 < s1 else "stabil")

    return {
        "distribution": dict(dist),
        "trend": trend,
        "dominant": dist.most_common(1)[0][0] if dist else None,
        "raw": mood_log
    }

# ====================================================
# B. TOPIC FREQUENCY
# ====================================================

def analisa_topik(top_n=5):
    """Return list topic paling sering muncul [(topic, count), ...]"""
    mm   = _get_mm()
    freq = mm.load_long().get("topic_freq", {})

    # Tambah dari short_term yang belum dipromote
    short_h = mm.load_short().get("history", [])
    for entry in short_h:
        for t in entry.get("tags", {}).get("topics", []):
            freq[t] = freq.get(t, 0) + 1

    return Counter(freq).most_common(top_n)

# ====================================================
# C. JAM AKTIF (ACTIVITY PATTERN)
# ====================================================

def analisa_jam_aktif():
    """Return jam paling aktif dan distribusi per jam."""
    history = _all_history()
    hours   = [_parse_hour(e.get("time","")) for e in history]
    hours   = [h for h in hours if h is not None]

    if not hours:
        return {"peak_hour": None, "label": "tidak ada data", "distribution": {}}

    dist      = dict(sorted(Counter(hours).items()))
    peak_hour = Counter(hours).most_common(1)[0][0]

    def label(h):
        if 5  <= h < 9:  return "Pagi"
        if 9  <= h < 12: return "Pagi siang"
        if 12 <= h < 15: return "Siang"
        if 15 <= h < 18: return "Sore"
        if 18 <= h < 21: return "Malam"
        return "Larut malam"

    return {
        "peak_hour"   : peak_hour,
        "label"       : label(peak_hour),
        "distribution": dist
    }

# ====================================================
# D. STREAK DETECTION
# ====================================================

def analisa_streak():
    """
    Return dict streak + warning status.
    Warning jika streak drop atau tidak aktif X hari.
    """
    mm     = _get_mm()
    streak = mm.load_long().get("streak", {})
    current = streak.get("current", 0)
    best    = streak.get("best", 0)
    last    = streak.get("last_date")

    # Cek berapa hari sejak terakhir aktif
    gap_days = 0
    if last:
        try:
            last_dt  = datetime.datetime.strptime(last, "%Y-%m-%d")
            gap_days = (datetime.datetime.now() - last_dt).days
        except Exception:
            pass

    warning = None
    if gap_days >= 3:
        warning = f"Lo tidak aktif {gap_days} hari. Streak terancam putus."
    elif gap_days == 2:
        warning = "Sudah 2 hari tidak aktif. Masuk sekarang sebelum streak putus."
    elif current > 0 and gap_days == 1:
        warning = "Belum aktif hari ini. Streak masih bisa dilanjutkan."

    return {
        "current"  : current,
        "best"     : best,
        "last_date": last,
        "gap_days" : gap_days,
        "warning"  : warning,
        "status"   : "aman" if gap_days == 0 else ("kritis" if gap_days >= 3 else "waspada")
    }

# ====================================================
# E. SARAN TAKTIS DINAMIS
# ====================================================

def generate_saran(stats, mood_data, streak_data, jam_data):
    """
    Generate saran berdasarkan data aktual, bukan hardcode angka.
    Return list string saran.
    """
    saran = []
    total = stats.get("total", 0)

    # ── Data terlalu sedikit ──
    if total < 5:
        saran.append("Data masih sangat tipis. Gunakan chatbot lebih sering supaya pola kebiasaan bisa terbaca.")
        return saran

    # ── Streak ────────────────────────────────────────────
    streak_warning = streak_data.get("warning")
    if streak_warning:
        saran.append(f"⚠ STREAK: {streak_warning}")

    current_streak = streak_data.get("current", 0)
    best_streak    = streak_data.get("best", 0)
    if current_streak >= 5:
        saran.append(f"🔥 Streak {current_streak} hari. Pertahankan — ini pola yang solid.")
    elif current_streak > 0 and best_streak > 0 and current_streak < best_streak // 2:
        saran.append(f"Streak lo ({current_streak} hari) masih jauh dari rekor terbaik ({best_streak} hari). Ada yang berubah?")

    # ── Mood ──────────────────────────────────────────────
    mood_trend = mood_data.get("trend", "stabil")
    mood_dom   = mood_data.get("dominant")
    mood_dist  = mood_data.get("distribution", {})

    if mood_trend == "memburuk":
        saran.append("📉 Mood lo cenderung memburuk dalam periode ini. Cek beban aktivitas atau pola tidur.")
    elif mood_trend == "membaik":
        saran.append("📈 Mood lo trend membaik. Pertahankan rutinitas yang sedang berjalan.")

    neg_count = mood_dist.get("negatif", 0)
    pos_count = mood_dist.get("positif", 0)
    if neg_count > pos_count and neg_count > 3:
        saran.append(f"Ada {neg_count} interaksi dengan mood negatif minggu ini. Pertimbangkan untuk set waktu recovery / istirahat.")

    # ── Jam aktif ─────────────────────────────────────────
    peak = jam_data.get("peak_hour")
    label = jam_data.get("label", "")
    if peak is not None:
        if 0 <= peak < 5:
            saran.append(f"Lo paling aktif jam {peak:02d}.00 (larut malam). Waspadai kualitas tidur dan fokus jangka panjang.")
        else:
            saran.append(f"Lo paling produktif di jam {peak:02d}.00 ({label}). Jadwalkan task penting di waktu ini.")

    # ── Volume interaksi ──────────────────────────────────
    short_count = stats.get("short_count", 0)
    if short_count > 20:
        saran.append("Short-term memory hampir penuh. Data akan segera dipromote ke long-term otomatis.")
    elif total > 50:
        saran.append(f"Lo sudah punya {total} data interaksi. Cek analisa mingguan tiap akhir minggu untuk ukur konsistensi.")

    # ── Topik dominan ─────────────────────────────────────
    top_topics = analisa_topik(top_n=2)
    if top_topics:
        top_str = ", ".join(f"'{t}' ({c}x)" for t, c in top_topics)
        saran.append(f"Topik paling sering: {top_str}. Ini yang paling banyak lo pikirkan/tanyakan.")

    if not saran:
        saran.append("Sistem berjalan normal. Terus gunakan bot secara konsisten.")

    return saran

# ====================================================
# F. WEEKLY SUMMARY (dipanggil oleh brain.py)
# ====================================================

def analisa_mingguan():
    """
    Return string ringkasan mingguan.
    Dipanggil langsung dari brain.py (interface lama tetap kompatibel).
    """
    history = _all_history()
    cutoff  = _n_days_ago(7)
    week_h  = [e for e in history if (e.get("time",""))[:10] >= cutoff]

    if not week_h:
        return "Belum ada aktivitas minggu ini."

    # Hari aktif
    active_days = len(set(_parse_date(e.get("time","")) for e in week_h if _parse_date(e.get("time",""))))

    # Topik
    topics = []
    for e in week_h:
        topics.extend(e.get("tags",{}).get("topics",[]))
    top_topics = Counter(topics).most_common(3)
    topic_str  = ", ".join(f"{t}({c})" for t,c in top_topics) if top_topics else "belum ada"

    # Mood
    moods    = [e.get("tags",{}).get("mood") for e in week_h if e.get("tags",{}).get("mood")]
    mood_str = Counter(moods).most_common(1)[0][0] if moods else "tidak terdeteksi"

    # Jam peak
    jam = analisa_jam_aktif()
    jam_str = f"jam {jam['peak_hour']:02d}.00 ({jam['label']})" if jam["peak_hour"] is not None else "belum terdeteksi"

    lines = [
        f"Periode  : 7 hari terakhir",
        f"Interaksi: {len(week_h)} entry  |  Hari aktif: {active_days}/7",
        f"Topik    : {topic_str}",
        f"Mood dom : {mood_str}",
        f"Jam aktif: {jam_str}",
    ]
    return "\n".join(lines)

# ====================================================
# G. ENTRY POINT
# ====================================================

def run():
    print("[Analyzer] Menjalankan analisis...")
    mm      = _get_mm()
    stats   = mm.memory_stats()
    mood    = analisa_mood()
    streak  = analisa_streak()
    jam     = analisa_jam_aktif()
    saran   = generate_saran(stats, mood, streak, jam)

    print(f"  Total interaksi : {stats['total']}")
    print(f"  Mood dominant   : {mood['dominant']} (trend: {mood['trend']})")
    print(f"  Streak          : {streak['current']} hari (status: {streak['status']})")
    if streak["warning"]:
        print(f"  ⚠ {streak['warning']}")
    print(f"  Jam paling aktif: {jam['peak_hour']} ({jam['label']})")
    print(f"  Saran:")
    for s in saran:
        print(f"    - {s}")
    print("[Analyzer] Done.")
