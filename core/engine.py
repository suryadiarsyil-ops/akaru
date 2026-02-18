# core/engine.py
# AKARU – Intent Router & Command Executor
# Lazy import untuk hemat RAM di startup

import os
from datetime import datetime
from core.config import DOCTRINE, LAZY_KEYWORDS, load_config, save_config
from core import memory as M
from core import display as D

# ── Help ──────────────────────────────────────────────────
def print_help():
    D.header("PERINTAH TERSEDIA", D.CYAN)
    cmds = [
        ("── CATATAN ──────────────────", ""),
        ("catat <teks>",         "Simpan catatan baru"),
        ("lihat catatan",        "Tampilkan semua catatan"),
        ("hapus catatan <no>",   "Hapus catatan"),
        ("── TUGAS ───────────────────", ""),
        ("tugas <teks>",         "Tambah tugas baru"),
        ("lihat tugas",          "Tampilkan semua tugas"),
        ("selesai <no>",         "Tandai tugas selesai"),
        ("hapus tugas <no>",     "Hapus tugas"),
        ("── MOOD & INSIGHT ─────────", ""),
        ("mood",                 "Check-in mood & energi hari ini"),
        ("lihat mood",           "Riwayat mood"),
        ("summary",              "Summary harian"),
        ("summary minggu",       "Summary mingguan"),
        ("analisis",             "Analisis produktivitas lokal"),
        ("── SISTEM ──────────────────", ""),
        ("cari <kata>",          "Cari di catatan & tugas"),
        ("status",               "Ringkasan sistem"),
        ("doktrin",              "Tampilkan doktrin"),
        ("goal",                 "Tampilkan goal aktif"),
        ("set goal <teks>",      "Ubah goal aktif"),
        ("set nama <nama>",      "Ganti username"),
        ("config",               "Lihat konfigurasi"),
        ("ekspor",               "Ekspor data ke TXT"),
        ("reset log",            "Hapus semua log"),
        ("lihat log",            "10 log terakhir"),
        ("bersih",               "Clear layar"),
        ("exit / quit",          "Keluar"),
    ]
    for cmd, desc in cmds:
        if desc == "":
            print(f"\n  {D.c(cmd, D.GRAY)}")
        else:
            print(f"  {D.c(cmd.ljust(24), D.GREEN)} {D.c(desc, D.GRAY)}")
    D.sep()

# ── Intent Router ────────────────────────────────────────
def route(text):
    t = text.lower().strip()

    if t.startswith(("catat ", "ingat ")):         return "NOTE"
    if t.startswith("tugas "):                      return "TASK_ADD"
    if t.startswith("selesai "):                    return "TASK_DONE"
    if t.startswith("hapus catatan"):               return "DEL_NOTE"
    if t.startswith("hapus tugas"):                 return "DEL_TASK"
    if t in ("lihat catatan", "catatan"):           return "VIEW_NOTES"
    if t in ("lihat tugas", "tugas"):               return "VIEW_TASKS"
    if t.startswith("lihat log") or t == "log":     return "VIEW_LOG"
    if t == "lihat mood":                           return "VIEW_MOOD"
    if t == "mood":                                 return "MOOD_CHECKIN"
    if t == "summary minggu":                       return "SUMMARY_WEEK"
    if t in ("summary", "ringkasan"):               return "SUMMARY_DAY"
    if t in ("analisis", "analyze", "insight"):     return "ANALYZE"
    if t == "status":                               return "STATUS"
    if t == "doktrin":                              return "DOCTRINE"
    if t == "goal":                                 return "GOAL"
    if t.startswith("set goal "):                   return "SET_GOAL"
    if t.startswith("set nama "):                   return "SET_NAME"
    if t == "config":                               return "CONFIG"
    if t.startswith("cari "):                       return "SEARCH"
    if t == "bersih":                               return "CLEAR"
    if t == "ekspor":                               return "EXPORT"
    if t == "reset log":                            return "RESET_LOG"
    if t in ("help", "bantuan", "?"):               return "HELP"
    return "UNKNOWN"

# ── Goal check ───────────────────────────────────────────
def violates_goal(text):
    return any(k in text.lower() for k in LAZY_KEYWORDS)

# ── Executor ─────────────────────────────────────────────
def execute(intent, text, state):
    """
    state = {cfg, memory, context, logs}
    Lazy import modul berat hanya saat dibutuhkan.
    """
    cfg  = state["cfg"]
    mem  = state["memory"]
    ctx  = state["context"]
    logs = state["logs"]
    t    = text.strip()

    # ── Catatan ───────────────────────────────────────────
    if intent == "NOTE":
        body = t[6:].strip() if t.lower().startswith("catat ") else t[6:].strip()
        if not body:
            D.err("Isi catatan tidak boleh kosong.")
            return
        note = M.add_note(mem, body)
        M.update_context(ctx, intent, note_text=body)
        D.ok(f"Catatan #{note['id']} disimpan.")

    elif intent == "VIEW_NOTES":
        notes = mem.get("notes", [])
        if not notes:
            D.dim("Belum ada catatan.")
            return
        D.header("CATATAN", D.CYAN)
        for n in notes:
            ts = D.c(f" {n['t'][:10]}", D.GRAY) if cfg.get("show_timestamps") else ""
            nid = D.c(f"#{n['id']}", D.MAGENTA, D.BOLD)
            print(f"  {nid}  {n['v']}{ts}")
        D.sep()

    elif intent == "DEL_NOTE":
        try:
            num = int(t.split()[-1])
        except ValueError:
            D.err("Format: hapus catatan <nomor>")
            return
        if cfg.get("strict_mode") and not D.confirm("Hapus catatan ini? (y/N): "):
            D.dim("Dibatalkan.")
            return
        if M.delete_note(mem, num):
            D.ok(f"Catatan #{num} dihapus.")
        else:
            D.err("Catatan tidak ditemukan.")

    # ── Tugas ─────────────────────────────────────────────
    elif intent == "TASK_ADD":
        body = t[6:].strip()
        if not body:
            D.err("Isi tugas tidak boleh kosong.")
            return
        task = M.add_task(mem, body)
        D.ok(f"Tugas #{task['id']} ditambahkan.")

    elif intent == "VIEW_TASKS":
        tasks = mem.get("tasks", [])
        if not tasks:
            D.dim("Belum ada tugas.")
            return
        D.header("TUGAS", D.CYAN)
        pending  = [t for t in tasks if not t.get("done")]
        done_lst = [t for t in tasks if t.get("done")]
        for tk in pending:
            ts  = D.c(f" {tk['t'][:10]}", D.GRAY) if cfg.get("show_timestamps") else ""
            tid = D.c(f"#{tk['id']}", D.YELLOW, D.BOLD)
            print(f"  {tid} {D.c('[ ]', D.GRAY)} {tk['v']}{ts}")
        for tk in done_lst:
            tid = D.c(f"#{tk['id']}", D.GRAY)
            print(f"  {tid} {D.c('[✓]', D.GREEN)} {D.c(tk['v'], D.GRAY)}")
        D.blank()
        D.dim(f"{len(pending)} aktif · {len(done_lst)} selesai")
        D.sep()

    elif intent == "TASK_DONE":
        try:
            num = int(t.split()[1])
        except (IndexError, ValueError):
            D.err("Format: selesai <nomor>")
            return
        tk = M.complete_task(mem, num)
        if tk:
            D.ok(f"Tugas #{num} '{tk['v'][:40]}' selesai! 🎉")
        else:
            D.err("Tugas tidak ditemukan.")

    elif intent == "DEL_TASK":
        try:
            num = int(t.split()[-1])
        except ValueError:
            D.err("Format: hapus tugas <nomor>")
            return
        if cfg.get("strict_mode") and not D.confirm("Hapus tugas ini? (y/N): "):
            D.dim("Dibatalkan.")
            return
        if M.delete_task(mem, num):
            D.ok(f"Tugas #{num} dihapus.")
        else:
            D.err("Tugas tidak ditemukan.")

    # ── Mood ──────────────────────────────────────────────
    elif intent == "MOOD_CHECKIN":
        from core.mood import prompt_mood
        prompt_mood()

    elif intent == "VIEW_MOOD":
        from core.mood import view_mood
        view_mood()

    # ── Summary ───────────────────────────────────────────
    elif intent == "SUMMARY_DAY":
        from core.summary import daily_summary
        daily_summary(mem, ctx)

    elif intent == "SUMMARY_WEEK":
        from core.summary import weekly_summary
        weekly_summary(mem, ctx)

    # ── Analyzer ──────────────────────────────────────────
    elif intent == "ANALYZE":
        from core.analyzer import show_analysis
        show_analysis(mem)

    # ── Status ────────────────────────────────────────────
    elif intent == "STATUS":
        from core.analyzer import productivity_score
        from core.mood import mood_stats
        ps    = productivity_score(mem)
        ms    = mood_stats()
        tasks = mem.get("tasks", [])
        D.header("STATUS SISTEM", D.CYAN)
        D.info("User",            cfg["username"])
        D.info("Session ke",      str(ctx.get("session_count", 1)))
        D.info("Streak aktif",    f"{ctx.get('streak_days', 0)} hari")
        D.blank()
        D.info("Catatan total",   str(len(mem.get("notes", []))))
        D.info("Tugas aktif",     str(len([t for t in tasks if not t.get("done")])))
        D.info("Tugas selesai",   str(len([t for t in tasks if t.get("done")])))
        D.blank()
        score = ps["score"]
        sc    = D.GREEN if score >= 70 else (D.YELLOW if score >= 40 else D.RED)
        D.info("Produktivitas",   D.c(f"{score}/100", sc, D.BOLD))
        if ms:
            D.info("Mood terakhir",   f"{ms['last_mood']}/5  Energi {ms['last_energy']}/5")
        if ctx.get("last_note"):
            D.blank()
            D.info("Catatan terakhir", D.c(ctx['last_note'][:40], D.GRAY))
        D.sep()

    elif intent == "LOG":
        pass  # handled below

    elif intent == "VIEW_LOG":
        if not logs:
            D.dim("Log kosong.")
            return
        D.header("LOG AKTIVITAS (10 terakhir)", D.CYAN)
        for e in logs[-10:]:
            s = D.c("OK", D.GREEN) if e.get("ok") else D.c("ERR", D.RED)
            print(f"  {D.c(e['t'], D.GRAY)}  [{s}]  {D.c(e.get('i','?'), D.YELLOW)}")
        D.sep()

    elif intent == "DOCTRINE":
        D.header("DOKTRIN AKARU", D.MAGENTA)
        for i, d in enumerate(DOCTRINE, 1):
            print(f"  {D.c(i, D.MAGENTA, D.BOLD)}.  {d}")
        D.sep()

    elif intent == "GOAL":
        D.header("GOAL AKTIF", D.YELLOW)
        print(f"  {cfg.get('goal')}")
        D.sep()

    elif intent == "SET_GOAL":
        body = t[9:].strip()
        if not body:
            D.err("Goal tidak boleh kosong.")
            return
        cfg["goal"] = body
        save_config(cfg)
        D.ok("Goal diperbarui.")

    elif intent == "SET_NAME":
        name = t[9:].strip()
        if not name:
            D.err("Nama tidak boleh kosong.")
            return
        cfg["username"] = name
        save_config(cfg)
        D.ok(f"Username → '{name}'")

    elif intent == "CONFIG":
        D.header("KONFIGURASI", D.CYAN)
        for k, v in cfg.items():
            D.info(k, str(v))
        D.sep()

    elif intent == "SEARCH":
        query = t[5:].strip().lower()
        if not query:
            D.err("Masukkan kata kunci.")
            return
        found = 0
        D.header(f"PENCARIAN: '{query}'", D.CYAN)
        for n in mem.get("notes", []):
            if query in n["v"].lower():
                print(f"  {D.c('Catatan', D.MAGENTA)} #{n['id']}: {n['v']}")
                found += 1
        for tk in mem.get("tasks", []):
            if query in tk["v"].lower():
                status = D.c("[✓]", D.GREEN) if tk.get("done") else D.c("[ ]", D.GRAY)
                print(f"  {D.c('Tugas', D.YELLOW)} #{tk['id']} {status}: {tk['v']}")
                found += 1
        D.sep()
        if found == 0:
            D.dim(f"Tidak ada hasil untuk '{query}'.")
        else:
            D.ok(f"{found} hasil ditemukan.")

    elif intent == "CLEAR":
        os.system("clear")
        from core.display import print_banner
        print_banner(cfg)

    elif intent == "EXPORT":
        _export(mem, cfg)

    elif intent == "RESET_LOG":
        if D.confirm("Reset semua log? (y/N): "):
            logs.clear()
            M.save_logs(logs)
            D.ok("Log direset.")
        else:
            D.dim("Dibatalkan.")

    elif intent == "HELP":
        print_help()

    else:
        D.dim("Perintah tidak dikenal. Ketik 'help'.")

# ── Export ───────────────────────────────────────────────
def _export(mem, cfg):
    from datetime import datetime
    fname = f"akaru_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    lines = [
        "AKARU CORE – Ekspor Data",
        f"Waktu  : {datetime.now().strftime('%d %b %Y %H:%M')}",
        f"User   : {cfg.get('username')}",
        "=" * 50, "",
        "CATATAN:",
    ]
    for n in mem.get("notes", []):
        lines.append(f"  #{n['id']} [{n['t']}] {n['v']}")
    lines += ["", "TUGAS:"]
    for tk in mem.get("tasks", []):
        s = "[✓]" if tk.get("done") else "[ ]"
        lines.append(f"  #{tk['id']} {s} [{tk['t']}] {tk['v']}")
    lines += ["", f"GOAL: {cfg.get('goal')}"]
    with open(fname, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    D.ok(f"Diekspor ke '{fname}'.")
