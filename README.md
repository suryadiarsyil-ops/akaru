# AKARU CORE v2.1.0
**Shadow Assistant Engine** — asisten pribadi offline untuk Termux di HP low-end.

> *Konsistensi lebih penting dari kenyamanan.*

---

## Spesifikasi Target
| Perangkat | Samsung Galaxy J2 Pro|
|-----------|----------------------|
| RAM       | ~1 GB                |
| Python    | 3.x (via Termux)     |
| Internet  | Tidak diperlukan     |
| Library eksternal | Tidak ada    |

---

## Struktur Project
```
akaru/
├── akaru.py          ← launcher utama
├── setup.sh          ← installer alias Termux
├── brain.py
├── data/             ← auto-generated (gitignored)
│   ├── memory.json
│   ├── log.json
│   ├── mood.json
│   ├── context.json
│   └── config.json
├── core/
│   ├── config.py     ← konstanta & load/save
│   ├── display.py    ← UI, warna ANSI, banner
│   ├── memory.py     ← cold memory + context sesi
│   ├── mood.py       ← mood & energy tracker
│   ├── analyzer.py   ← analisis pola lokal (no ML)
│   ├── summary.py    ← summary harian & mingguan
│   └── engine.py     ← intent router + executor
└── modules/
    ├── __init__.py
    ├── analyzer.py
    └── memory_manager.py
```

---

## Instalasi di Termux

```bash
# 1. Install Python (jika belum)
pkg install python git

# 2. Clone repo
git clone https://github.com/suryadiarsyil-ops/akaru.git
cd akaru

# 3. Setup alias
bash setup.sh

# 4. Reload shell
source ~/.bashrc

# 5. Jalankan
akaru
```

---

## Perintah

### Catatan
| Perintah | Fungsi |
|----------|--------|
| `catat <teks>` | Simpan catatan baru |
| `lihat catatan` | Tampilkan semua catatan |
| `hapus catatan <no>` | Hapus catatan |

### Tugas
| Perintah | Fungsi |
|----------|--------|
| `tugas <teks>` | Tambah tugas baru |
| `lihat tugas` | Tampilkan semua tugas |
| `selesai <no>` | Tandai tugas selesai |
| `hapus tugas <no>` | Hapus tugas |

### Mood & Insight
| Perintah | Fungsi |
|----------|--------|
| `mood` | Check-in mood & energi hari ini |
| `lihat mood` | Riwayat mood |
| `summary` | Summary harian otomatis |
| `summary minggu` | Summary mingguan |
| `analisis` | Analisis produktivitas lokal |

### Sistem
| Perintah | Fungsi |
|----------|--------|
| `status` | Ringkasan sistem + skor produktivitas |
| `cari <kata>` | Cari di catatan & tugas |
| `set goal <teks>` | Ubah goal aktif |
| `set nama <nama>` | Ganti username |
| `ekspor` | Ekspor semua data ke TXT |
| `bersih` | Clear layar |
| `exit` | Keluar |

---

## Fitur Utama

### Memory Layer
- **Cold memory**: catatan & tugas tersimpan permanen di `data/memory.json`
- **Context sesi**: AKARU ingat kapan terakhir aktif, intent terakhir, streak hari

### Analyzer Lokal
Tanpa ML, tanpa library eksternal. Hitung dari data JSON:
- **Skor produktivitas** (0–100) dari rasio tugas, catatan aktif, streak
- **Pola jam aktif** dari distribusi log
- **Korelasi mood vs produktivitas**

### Summary Otomatis
- **Harian**: catatan, tugas selesai/ditambah/pending, mood, streak
- **Mingguan**: ringkasan 7 hari, hari paling produktif, rata-rata mood

### Mood & Energy Tracker
- Input manual skala 1–5
- Catatan singkat opsional
- Terintegrasi dengan summary & analyzer

### Goal Enforcement
Kata kunci malas (`nanti saja`, `skip`, dll.) ditolak saat input catatan/tugas.

---

## Data & Privacy
Semua data tersimpan lokal di folder `data/`. Tidak ada koneksi internet sama sekali.

```
.gitignore sudah mengecualikan folder data/
```

---

## Doktrin
1. Konsistensi lebih penting dari kenyamanan
2. Tujuan jangka panjang mengalahkan impuls
3. Sistem tidak tunduk pada emosi

---

*Built for Samsung Galaxy J2 Pro + Termux. No internet. No ML. Just discipline.*
# akaru
