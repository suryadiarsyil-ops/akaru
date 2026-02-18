#!/usr/bin/env python3
# akaru.py – AKARU CORE Launcher
# Jalankan: python akaru.py
# Atau lewat alias: akaru (setelah setup.sh)

import os
import sys

# Pastikan direktori project ada di path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.config import load_config, ensure_data_dir
from core import display as D
from core import memory as M
from core.engine import route, execute, violates_goal, print_help

def main():
    ensure_data_dir()

    # Load semua state sekali di awal
    cfg     = load_config()
    mem     = M.load_memory()
    ctx     = M.load_context()
    logs    = M.load_logs()

    D.set_color(cfg.get("color", True))

    # Update sesi
    M.start_session(ctx)

    # Banner
    os.system("clear")
    D.print_banner(cfg)

    # Greeting kontekstual
    _greet(ctx, cfg)

    state = {"cfg": cfg, "memory": mem, "context": ctx, "logs": logs}

    # ── Main loop ──────────────────────────────────────────
    while True:
        try:
            prompt = D.c(f"\n  {cfg['username']} ❯ ", D.CYAN, D.BOLD)
            user_input = input(prompt).strip()
        except (EOFError, KeyboardInterrupt):
            print(D.c("\n\n  Stay consistent. AKARU offline.\n", D.GRAY))
            break

        if not user_input:
            continue

        if user_input.lower() in ("exit", "quit", "keluar", "q"):
            print(D.c("\n  AKARU offline. Tetap konsisten.\n", D.CYAN, D.BOLD))
            break

        intent = route(user_input)

        # Goal enforcement — hanya untuk input konten
        if intent in ("NOTE", "TASK_ADD") and violates_goal(user_input):
            D.warn("Ditahan: bertentangan dengan goal aktif.")
            M.append_log(logs, intent, ok=False, note="goal_violation",
                         max_logs=cfg.get("max_logs", 80))
            continue

        execute(intent, user_input, state)
        M.append_log(logs, intent, ok=True, max_logs=cfg.get("max_logs", 80))
        M.update_context(ctx, intent)

# ── Greeting kontekstual ──────────────────────────────────
def _greet(ctx, cfg):
    from datetime import datetime
    name    = cfg.get("username", "User")
    streak  = ctx.get("streak_days", 0)
    scount  = ctx.get("session_count", 1)
    last    = ctx.get("last_active")
    hour    = datetime.now().hour

    # Salam berdasarkan waktu
    if   hour < 5:  salam = "Masih begadang"
    elif hour < 11: salam = "Selamat pagi"
    elif hour < 15: salam = "Selamat siang"
    elif hour < 18: salam = "Selamat sore"
    else:           salam = "Selamat malam"

    print(D.c(f"  {salam}, {name}.", D.WHITE, D.BOLD))

    if streak >= 3:
        print(D.c(f"  🔥 Streak {streak} hari. Pertahankan.", D.YELLOW))
    if scount == 1:
        print(D.c("  Sesi pertama. Sistem siap.", D.GRAY))
    elif last:
        try:
            from datetime import timedelta
            last_dt = datetime.fromisoformat(last)
            diff    = datetime.now() - last_dt
            if diff.days >= 1:
                print(D.c(f"  Terakhir aktif {diff.days} hari lalu. Ayo kembali ke jalur.", D.GRAY))
            else:
                hrs = diff.seconds // 3600
                print(D.c(f"  Terakhir aktif {hrs} jam lalu.", D.GRAY))
        except Exception:
            pass

    D.blank()

if __name__ == "__main__":
    main()
