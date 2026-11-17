"""
schedule.py
-----------
Modul ini menyimpan dan mengelola data jadwal kuliah Kelas F UIN Syarif
Hidayatullah Jakarta. Semua data bersifat statis (hardcoded) sesuai
database yang diberikan dan TIDAK boleh diubah namanya, jamnya, maupun
ruangannya.

Modul ini juga menyediakan fungsi-fungsi bantu (helper functions) yang
dipakai oleh chatbot.py untuk menjawab pertanyaan seputar jadwal, seperti:
- Mendapatkan jadwal hari ini / hari tertentu
- Mencari mata kuliah berdasarkan nama
- Mencari ruangan berdasarkan nama mata kuliah
- Mengecek status perkuliahan (sebelum/sedang/sesudah kuliah)
- Mendapatkan mata kuliah terakhir dalam seminggu

Aplikasi TIDAK boleh mengarang data jadwal, dosen, atau ruangan yang
tidak ada di sini.
"""

from __future__ import annotations

import datetime
from typing import Optional

# ---------------------------------------------------------------------
# DATABASE JADWAL KULIAH (SUMBER KEBENARAN / SOURCE OF TRUTH)
# ---------------------------------------------------------------------
# Struktur: { "HARI": [ {matkul, jam_mulai, jam_selesai, ruang}, ... ] }
# Jam disimpan sebagai string "HH.MM" sesuai format pada dokumen asli,
# dan juga sebagai objek datetime.time untuk keperluan perhitungan.

SCHEDULE: dict[str, list[dict]] = {
    "SENIN": [
        {
            "matkul": "Literasi Digital",
            "jam_mulai": "10.10",
            "jam_selesai": "11.50",
            "ruang": "B.604",
        },
    ],
    "SELASA": [
        {
            "matkul": "Studi Islam",
            "jam_mulai": "07.30",
            "jam_selesai": "10.50",
            "ruang": "B.603",
        },
        {
            "matkul": "Praktikum Qira'ah dan Ibadah",
            "jam_mulai": "11.00",
            "jam_selesai": "12.40",
            "ruang": "A.608",
        },
        {
            "matkul": "Pendidikan Kewarganegaraan",
            "jam_mulai": "13.30",
            "jam_selesai": "15.10",
            "ruang": "A.704",
        },
    ],
    "RABU": [],  # Tidak ada jadwal kuliah
    "KAMIS": [
        {
            "matkul": "Matematika Diskrit",
            "jam_mulai": "07.30",
            "jam_selesai": "10.50",
            "ruang": "A.705",
        },
        {
            "matkul": "Dasar-Dasar Pemrograman",
            "jam_mulai": "13.30",
            "jam_selesai": "16.00",
            "ruang": "B.602",
        },
    ],
    "JUMAT": [
        {
            "matkul": "Bahasa Inggris",
            "jam_mulai": "07.30",
            "jam_selesai": "10.00",
            "ruang": "B.602",
        },
    ],
    "SABTU": [],  # Tidak ada jadwal kuliah
    "MINGGU": [],  # Tidak ada jadwal kuliah
}

# Urutan hari standar (Senin = 0, ... Minggu = 6) mengikuti Python's weekday()
HARI_URUTAN = ["SENIN", "SELASA", "RABU", "KAMIS", "JUMAT", "SABTU", "MINGGU"]

# Alias penamaan hari agar pencocokan bahasa sehari-hari lebih fleksibel
HARI_ALIAS = {
    "senin": "SENIN",
    "selasa": "SELASA",
    "rabu": "RABU",
    "kamis": "KAMIS",
    "jumat": "JUMAT",
    "jum'at": "JUMAT",
    "jum at": "JUMAT",
    "sabtu": "SABTU",
    "minggu": "MINGGU",
    "ahad": "MINGGU",
}


# ---------------------------------------------------------------------
# UTIL WAKTU
# ---------------------------------------------------------------------

def _parse_jam(jam_str: str) -> datetime.time:
    """Mengubah string jam format 'HH.MM' menjadi objek datetime.time."""
    jam_str = jam_str.replace(".", ":")
    hh, mm = jam_str.split(":")
    return datetime.time(int(hh), int(mm))


def get_hari_ini() -> str:
    """Mengembalikan nama hari ini (huruf besar) berdasarkan waktu WIB."""
    now = get_waktu_sekarang()
    return HARI_URUTAN[now.weekday()]


def get_waktu_sekarang() -> datetime.datetime:
    """
    Mengembalikan waktu saat ini dalam zona WIB (UTC+7).
    Tidak bergantung pada library pihak ketiga agar tetap ringan dan
    tidak error jika modul zoneinfo/pytz tidak tersedia di environment.
    """
    utc_now = datetime.datetime.utcnow()
    wib_now = utc_now + datetime.timedelta(hours=7)
    return wib_now


def normalisasi_nama_hari(teks: str) -> Optional[str]:
    """Mencoba mengenali nama hari dari potongan teks bebas pengguna."""
    teks_lower = teks.lower()
    for alias, hari_resmi in HARI_ALIAS.items():
        if alias in teks_lower:
            return hari_resmi
    return None


# ---------------------------------------------------------------------
# FUNGSI UTAMA JADWAL
# ---------------------------------------------------------------------

def get_jadwal_hari(hari: str) -> list[dict]:
    """Mengembalikan list jadwal untuk hari tertentu (format nama resmi)."""
    hari = hari.upper()
    return SCHEDULE.get(hari, [])


def get_jadwal_mingguan() -> dict[str, list[dict]]:
    """Mengembalikan seluruh jadwal kuliah dalam seminggu."""
    return SCHEDULE


def cari_matkul(nama_matkul: str) -> list[dict]:
    """
    Mencari mata kuliah berdasarkan nama (pencocokan sebagian, tidak
    case-sensitive). Mengembalikan list hasil berisi hari + detail jadwal.
    """
    hasil = []
    kata_kunci = nama_matkul.strip().lower()
    for hari, daftar in SCHEDULE.items():
        for item in daftar:
            if kata_kunci in item["matkul"].lower():
                hasil.append({"hari": hari, **item})
    return hasil


def cari_ruangan(nama_matkul: str) -> Optional[str]:
    """Mengembalikan ruangan dari mata kuliah tertentu, jika ditemukan."""
    hasil = cari_matkul(nama_matkul)
    if hasil:
        return hasil[0]["ruang"]
    return None


def hitung_jumlah_matkul(hari: str) -> int:
    """Menghitung jumlah mata kuliah pada hari tertentu."""
    return len(get_jadwal_hari(hari))


def get_matkul_terakhir_minggu_ini() -> Optional[dict]:
    """
    Mengembalikan mata kuliah terakhir dalam satu minggu, dilihat dari
    hari dengan urutan paling akhir yang memiliki jadwal (Senin-Minggu),
    diambil dari jam selesai paling akhir pada hari tersebut.
    """
    for hari in reversed(HARI_URUTAN):
        daftar = SCHEDULE.get(hari, [])
        if daftar:
            matkul_terakhir = max(
                daftar, key=lambda item: _parse_jam(item["jam_selesai"])
            )
            return {"hari": hari, **matkul_terakhir}
    return None


def status_perkuliahan_sekarang() -> dict:
    """
    Mengecek status mahasiswa saat ini terhadap jadwal hari ini:
    - "sebelum_kuliah": belum ada kelas yang dimulai
    - "sedang_kuliah": sedang berada dalam jam kelas tertentu
    - "jeda": di antara dua kelas hari ini
    - "setelah_kuliah": semua kelas hari ini sudah selesai
    - "libur": tidak ada jadwal sama sekali hari ini

    Mengembalikan dict berisi status dan detail kelas terkait (jika ada).
    """
    now = get_waktu_sekarang()
    hari_ini = get_hari_ini()
    jadwal = get_jadwal_hari(hari_ini)

    if not jadwal:
        return {"status": "libur", "hari": hari_ini, "kelas": None}

    waktu_now = now.time()
    jadwal_terurut = sorted(jadwal, key=lambda i: _parse_jam(i["jam_mulai"]))

    for kelas in jadwal_terurut:
        mulai = _parse_jam(kelas["jam_mulai"])
        selesai = _parse_jam(kelas["jam_selesai"])
        if mulai <= waktu_now <= selesai:
            return {"status": "sedang_kuliah", "hari": hari_ini, "kelas": kelas}

    if waktu_now < _parse_jam(jadwal_terurut[0]["jam_mulai"]):
        return {
            "status": "sebelum_kuliah",
            "hari": hari_ini,
            "kelas": jadwal_terurut[0],
        }

    if waktu_now > _parse_jam(jadwal_terurut[-1]["jam_selesai"]):
        return {
            "status": "setelah_kuliah",
            "hari": hari_ini,
            "kelas": jadwal_terurut[-1],
        }

    # Berada di antara dua kelas (jeda)
    kelas_berikutnya = None
    for kelas in jadwal_terurut:
        if waktu_now < _parse_jam(kelas["jam_mulai"]):
            kelas_berikutnya = kelas
            break
    return {"status": "jeda", "hari": hari_ini, "kelas": kelas_berikutnya}


def format_jadwal_harian(hari: str) -> str:
    """Mengubah jadwal satu hari menjadi teks yang mudah dibaca."""
    hari = hari.upper()
    jadwal = get_jadwal_hari(hari)
    if not jadwal:
        return f"Hari {hari.capitalize()} nggak ada jadwal kuliah. Santuy dulu ya! 😄"

    baris = [f"📅 Jadwal kuliah hari {hari.capitalize()}:"]
    for item in jadwal:
        baris.append(
            f"- {item['matkul']} | {item['jam_mulai']}–{item['jam_selesai']} WIB | Ruang {item['ruang']}"
        )
    return "\n".join(baris)


def format_jadwal_mingguan() -> str:
    """Mengubah seluruh jadwal mingguan menjadi teks yang mudah dibaca."""
    baris = ["📋 Jadwal Kuliah Mingguan Kelas F:"]
    for hari in HARI_URUTAN:
        jadwal = SCHEDULE.get(hari, [])
        baris.append(f"\n**{hari.capitalize()}**")
        if not jadwal:
            baris.append("  Tidak ada jadwal kuliah.")
        else:
            for item in jadwal:
                baris.append(
                    f"  - {item['matkul']} | {item['jam_mulai']}–{item['jam_selesai']} WIB | Ruang {item['ruang']}"
                )
    return "\n".join(baris)
