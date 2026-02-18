#!/data/data/com.termux/files/usr/bin/bash
# setup.sh – AKARU Setup Script untuk Termux
# Jalankan sekali: bash setup.sh

AKARU_DIR="$(cd "$(dirname "$0")" && pwd)"
BASHRC="$HOME/.bashrc"
ALIAS_LINE="alias akaru='python $AKARU_DIR/akaru.py'"

echo ""
echo "  ╔══════════════════════════════╗"
echo "  ║     AKARU SETUP – Termux     ║"
echo "  ╚══════════════════════════════╝"
echo ""

# ── Cek Python ───────────────────────────────────────────
if ! command -v python &> /dev/null; then
    echo "  [!] Python tidak ditemukan."
    echo "      Install dulu: pkg install python"
    exit 1
fi

PY_VER=$(python --version 2>&1)
echo "  [✓] Python ditemukan: $PY_VER"

# ── Buat folder data ──────────────────────────────────────
mkdir -p "$AKARU_DIR/data"
echo "  [✓] Folder data/ siap: $AKARU_DIR/data"

# ── Tambah alias ke .bashrc ───────────────────────────────
if grep -q "alias akaru=" "$BASHRC" 2>/dev/null; then
    echo "  [~] Alias 'akaru' sudah ada di .bashrc, diperbarui."
    # Hapus baris lama
    sed -i '/alias akaru=/d' "$BASHRC"
fi

echo "" >> "$BASHRC"
echo "# AKARU – Shadow Assistant" >> "$BASHRC"
echo "$ALIAS_LINE" >> "$BASHRC"
echo "  [✓] Alias ditambahkan ke $BASHRC"

# ── Tambah alias akaru-log ────────────────────────────────
LOG_ALIAS="alias akaru-log='cat $AKARU_DIR/data/log.json | python -m json.tool | tail -40'"
if ! grep -q "alias akaru-log=" "$BASHRC" 2>/dev/null; then
    echo "$LOG_ALIAS" >> "$BASHRC"
    echo "  [✓] Alias 'akaru-log' ditambahkan."
fi

# ── Selesai ───────────────────────────────────────────────
echo ""
echo "  Setup selesai!"
echo ""
echo "  Jalankan sekarang:"
echo "    source ~/.bashrc"
echo "    akaru"
echo ""
echo "  Atau langsung:"
echo "    python $AKARU_DIR/akaru.py"
echo ""
