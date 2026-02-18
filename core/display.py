# core/display.py
# AKARU – UI, Warna, Banner
# Dioptimasi untuk Termux di HP low-end (no heavy rendering)

import sys
import os
import shutil
from datetime import datetime
from core.config import VERSION, APP_NAME, TAGLINE

# ── ANSI ──────────────────────────────────────────────────
# Termux di Android mendukung ANSI standar
RESET   = "\033[0m"
BOLD    = "\033[1m"
DIM     = "\033[2m"
RED     = "\033[91m"
GREEN   = "\033[92m"
YELLOW  = "\033[93m"
BLUE    = "\033[94m"
MAGENTA = "\033[95m"
CYAN    = "\033[96m"
WHITE   = "\033[97m"
GRAY    = "\033[90m"

_use_color = True  # diset dari engine berdasarkan config

def set_color(enabled: bool):
    global _use_color
    _use_color = enabled

def c(text, *codes):
    if not _use_color:
        return str(text)
    return "".join(codes) + str(text) + RESET

def tw():
    """Terminal width, fallback 58 (aman di J2 Pro)"""
    return min(shutil.get_terminal_size((58, 20)).columns, 58)

def sep(char="─", color=GRAY):
    print(c(char * tw(), color))

def blank():
    print()

def header(title, color=CYAN):
    sep("─", color)
    print(c(f"  {title}", color, BOLD))
    sep("─", color)

def info(label, value, label_w=24):
    print(f"  {c(label.ljust(label_w), GRAY)} {c(value, WHITE)}")

def ok(msg):
    print(c(f"  ✓  {msg}", GREEN))

def err(msg):
    print(c(f"  ✗  {msg}", RED))

def warn(msg):
    print(c(f"  ⚠  {msg}", YELLOW))

def dim(msg):
    print(c(f"  –  {msg}", GRAY))

def tag(label, color=MAGENTA):
    return c(f"[{label}]", color)

# ── Banner ────────────────────────────────────────────────
def print_banner(cfg):
    goal = cfg.get("goal", "")
    goal_short = goal[:46] + ".." if len(goal) > 48 else goal

    print()
    print(c("  ╔═══════════════════════════════════╗", CYAN))
    print(c("  ║  ", CYAN) + c(f"{'AKARU':^33}", CYAN, BOLD) + c("║", CYAN))
    print(c("  ║  ", CYAN) + c(f"{TAGLINE:^33}", GRAY)       + c("║", CYAN))
    print(c("  ║  ", CYAN) + c(f"{'v' + VERSION:^33}", DIM)  + c("║", CYAN))
    print(c("  ╚═══════════════════════════════════╝", CYAN))
    blank()
    print(f"  {c('User  :', GRAY)} {c(cfg['username'], WHITE, BOLD)}")
    print(f"  {c('Goal  :', GRAY)} {c(goal_short, YELLOW)}")
    print(f"  {c('Waktu :', GRAY)} {c(now_pretty(), GRAY)}")
    sep("─", CYAN)
    print(f"  {c('help', GREEN)} – daftar perintah  |  {c('exit', RED)} – keluar")
    sep()
    blank()

# ── Time ──────────────────────────────────────────────────
def now_pretty():
    return datetime.now().strftime("%d %b %Y, %H:%M")

def confirm(prompt="Yakin? (y/N): "):
    try:
        ans = input(c(f"  ⚠  {prompt}", YELLOW)).strip().lower()
        return ans in ("y", "ya", "yes")
    except (EOFError, KeyboardInterrupt):
        return False
