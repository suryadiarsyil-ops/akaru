# core/config.py
# AKARU – Konfigurasi & Konstanta Global

import json
import os

VERSION     = "2.1.0"
APP_NAME    = "AKARU"
TAGLINE     = "Shadow Assistant Engine"

# ── Path ──────────────────────────────────────────────────
BASE_DIR    = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR    = os.path.join(BASE_DIR, "data")
MEMORY_FILE = os.path.join(DATA_DIR, "memory.json")
LOG_FILE    = os.path.join(DATA_DIR, "log.json")
CONTEXT_FILE= os.path.join(DATA_DIR, "context.json")
MOOD_FILE   = os.path.join(DATA_DIR, "mood.json")
CONFIG_FILE = os.path.join(DATA_DIR, "config.json")

# ── Defaults ──────────────────────────────────────────────
DEFAULT_CONFIG = {
    "username"        : "User",
    "strict_mode"     : True,
    "max_logs"        : 80,
    "show_timestamps" : True,
    "color"           : True,
    "goal"            : "Bangun asisten pribadi stabil di HP low-end sebelum pindah ke PC",
}

DOCTRINE = [
    "Konsistensi lebih penting dari kenyamanan",
    "Tujuan jangka panjang mengalahkan impuls",
    "Sistem tidak tunduk pada emosi",
]

LAZY_KEYWORDS = [
    "nanti saja", "malas", "bebas", "skip",
    "males", "ah sudah", "gak mau", "ga mau",
]

# ── Util ──────────────────────────────────────────────────
def ensure_data_dir():
    os.makedirs(DATA_DIR, exist_ok=True)

def load_json(path, default):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return default if not callable(default) else default()

def save_json(path, data):
    ensure_data_dir()
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def load_config():
    cfg = load_json(CONFIG_FILE, {})
    for k, v in DEFAULT_CONFIG.items():
        cfg.setdefault(k, v)
    return cfg

def save_config(cfg):
    save_json(CONFIG_FILE, cfg)
