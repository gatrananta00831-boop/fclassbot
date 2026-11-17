"""
chatbot.py
----------
Modul "otak" dari FClassBot. Bertanggung jawab untuk:

1. Memahami pertanyaan pengguna (bahasa Indonesia sehari-hari) melalui
   pendekatan rule-based / keyword matching terhadap data jadwal di
   schedule.py. Ini memastikan pertanyaan seputar jadwal SELALU terjawab
   dengan benar dan konsisten, tanpa tergantung pada API AI eksternal.

2. Jika pertanyaan tidak berkaitan dengan jadwal kuliah, dan API Gemini
   tersedia (API key valid), pertanyaan akan diteruskan ke Google Gemini
   API untuk mendapatkan jawaban AI umum.

3. Jika API Gemini tidak tersedia / error / tidak dikonfigurasi, chatbot
   tetap bisa menjawab pertanyaan seputar jadwal (fallback lokal), dan
   akan memberi tahu pengguna dengan sopan bahwa fitur AI umum sedang
   tidak tersedia untuk pertanyaan di luar topik jadwal.

Chatbot TIDAK PERNAH mengarang data jadwal, dosen, atau ruangan yang
tidak ada di database schedule.py.
"""

from __future__ import annotations

import logging
from typing import Optional

import schedule as sch

logger = logging.getLogger("fclassbot.chatbot")
logger.setLevel(logging.INFO)

# ---------------------------------------------------------------------
# KONFIGURASI GEMINI (DIMUAT SECARA LAZY / OPSIONAL)
# ---------------------------------------------------------------------
# Library google-generativeai bersifat opsional: jika tidak terpasang
# atau API key tidak tersedia, aplikasi tetap berjalan normal untuk
# fitur jadwal (sesuai requirement "harus dapat digunakan meskipun API
# AI tidak tersedia").

try:
    import google.generativeai as genai

    _GENAI_AVAILABLE = True
except ImportError:  # pragma: no cover
    _GENAI_AVAILABLE = False


class GeminiClient:
    """Wrapper tipis di sekitar Google Gemini API (free tier)."""

    def __init__(self, api_key: Optional[str]):
        self.api_key = api_key
        self.model = None
        self.enabled = False

        if not _GENAI_AVAILABLE:
            logger.warning("Library google-generativeai tidak terpasang.")
            return

        if not api_key:
            logger.warning("GEMINI_API_KEY tidak ditemukan di Secrets/ENV.")
            return

        try:
            genai.configure(api_key=api_key)
            # "gemini-1.5-flash" dipilih karena termasuk dalam free tier
            # Google AI Studio dan cukup cepat untuk chatbot interaktif.
            self.model = genai.GenerativeModel("gemini-1.5-flash")
            self.enabled = True
        except Exception as exc:  # noqa: BLE001
            logger.error("Gagal inisialisasi Gemini API: %s", exc)
            self.enabled = False

    def ask(self, prompt: str) -> str:
        """Mengirim prompt ke Gemini API dan mengembalikan teks jawaban."""
        if not self.enabled or self.model is None:
            return (
                "Maaf, fitur AI umum FClassBot sedang tidak tersedia saat ini "
                "(API key belum terpasang atau sedang bermasalah). "
                "Tapi aku tetap bisa bantu jawab soal jadwal kuliah kok! 😊"
            )
        try:
            system_context = (
                "Kamu adalah FClassBot, asisten AI untuk mahasiswa Kelas F "
                "UIN Syarif Hidayatullah Jakarta. Jawablah dengan bahasa "
                "Indonesia yang ramah, santai tapi tetap sopan dan informatif. "
                "Jawaban singkat, padat, jelas.\n\n"
                f"Pertanyaan mahasiswa: {prompt}"
            )
            response = self.model.generate_content(system_context)
            text = getattr(response, "text", None)
            if not text:
                return "Maaf, aku belum bisa memproses pertanyaan itu. Coba tanya dengan cara lain, ya."
            return text.strip()
        except Exception as exc:  # noqa: BLE001
            logger.error("Gemini API error: %s", exc)
            return (
                "Waduh, lagi ada gangguan saat menghubungi AI. "
                "Coba lagi beberapa saat ya, atau tanyakan soal jadwal kuliah dulu! 🙏"
            )


# ---------------------------------------------------------------------
# PEMAHAMAN PERTANYAAN SEPUTAR JADWAL (RULE-BASED)
# ---------------------------------------------------------------------

SAPAAN = ["halo", "hai", "hi", "hello", "pagi", "siang", "sore", "malam", "p"]

KATA_KUNCI_HARI_INI = ["hari ini", "sekarang"]
KATA_KUNCI_BESOK = ["besok", "esok"]
KATA_KUNCI_MINGGUAN = [
    "jadwal minggu",
    "jadwal mingguan",
    "seminggu",
    "semua jadwal",
    "jadwal lengkap",
    "jadwal kuliah apa saja",
]
KATA_KUNCI_LIBUR = ["libur", "kosong", "tidak ada kuliah", "nggak ada kuliah"]
KATA_KUNCI_TERAKHIR = ["terakhir minggu ini", "mata kuliah terakhir", "kuliah terakhir"]
KATA_KUNCI_JUMLAH = ["berapa mata kuliah", "ada berapa kuliah", "jumlah mata kuliah"]
KATA_KUNCI_RUANGAN = ["ruang", "ruangan", "di mana", "dimana"]
KATA_KUNCI_JAM = ["jam berapa", "pukul berapa", "mulai jam", "masuk jam"]
KATA_KUNCI_STATUS = [
    "sedang kuliah",
    "lagi kuliah",
    "masih kuliah",
    "sudah selesai kuliah",
    "udah selesai kuliah",
]
KATA_KUNCI_BANTUAN = ["bantuan", "help", "bisa apa", "fitur apa"]


def _hari_besok() -> str:
    idx = sch.HARI_URUTAN.index(sch.get_hari_ini())
    return sch.HARI_URUTAN[(idx + 1) % 7]


def _cocok_kata_kunci(teks: str, daftar_kata_kunci: list[str]) -> bool:
    return any(k in teks for k in daftar_kata_kunci)


def _ekstrak_nama_matkul_dari_teks(teks: str) -> Optional[str]:
    """
    Mencoba mencocokkan teks pengguna dengan salah satu nama mata kuliah
    yang ada di database, dengan pencocokan sebagian (substring) yang
    tidak case-sensitive.
    """
    teks_lower = teks.lower()
    semua_matkul = set()
    for daftar in sch.SCHEDULE.values():
        for item in daftar:
            semua_matkul.add(item["matkul"])

    # Coba cocokkan nama matkul penuh atau sebagian kata kuncinya
    for matkul in semua_matkul:
        if matkul.lower() in teks_lower:
            return matkul

    # Coba cocokkan per-kata (misal "diskrit" -> "Matematika Diskrit")
    for matkul in semua_matkul:
        kata_kata = matkul.lower().split()
        for kata in kata_kata:
            if len(kata) > 3 and kata in teks_lower:
                return matkul
    return None


def jawab_pertanyaan_jadwal(teks: str) -> Optional[str]:
    """
    Mencoba menjawab pertanyaan pengguna HANYA menggunakan data jadwal
    lokal (schedule.py). Mengembalikan None jika pertanyaan tidak
    dikenali sebagai pertanyaan seputar jadwal, sehingga bisa diteruskan
    ke Gemini API (jika tersedia) sebagai jawaban AI umum.
    """
    teks_lower = teks.lower().strip()

    if not teks_lower:
        return None

    # --- Sapaan sederhana ---
    if teks_lower in SAPAAN or any(teks_lower.startswith(s) for s in SAPAAN):
        return (
            "Halo! 👋 Aku FClassBot, asisten kelas buat Kelas F. "
            "Kamu bisa tanya soal jadwal kuliah, misalnya 'hari ini kuliah apa?' "
            "atau pakai tombol Quick Questions di bawah. Ada yang bisa aku bantu?"
        )

    # --- Bantuan ---
    if _cocok_kata_kunci(teks_lower, KATA_KUNCI_BANTUAN):
        return (
            "Aku bisa bantu kamu seputar:\n"
            "- 📅 Jadwal kuliah hari ini / hari tertentu\n"
            "- 📋 Jadwal kuliah mingguan lengkap\n"
            "- 🔍 Cari jadwal berdasarkan nama mata kuliah\n"
            "- 🏫 Cari ruangan kelas\n"
            "- ⏰ Status kuliah (sebelum/sedang/habis kuliah)\n\n"
            "Contoh: 'Matematika Diskrit di ruangan mana?' atau 'besok kuliah jam berapa?'"
        )

    # --- Jadwal mingguan ---
    if _cocok_kata_kunci(teks_lower, KATA_KUNCI_MINGGUAN):
        return sch.format_jadwal_mingguan()

    # --- Mata kuliah terakhir minggu ini ---
    if _cocok_kata_kunci(teks_lower, KATA_KUNCI_TERAKHIR):
        terakhir = sch.get_matkul_terakhir_minggu_ini()
        if terakhir:
            return (
                f"Mata kuliah terakhir minggu ini adalah **{terakhir['matkul']}** "
                f"pada hari {terakhir['hari'].capitalize()}, jam "
                f"{terakhir['jam_mulai']}–{terakhir['jam_selesai']} WIB di ruang {terakhir['ruang']}."
            )
        return "Belum ada data mata kuliah untuk minggu ini."

    # --- Jumlah mata kuliah pada hari tertentu ---
    if _cocok_kata_kunci(teks_lower, KATA_KUNCI_JUMLAH):
        hari = sch.normalisasi_nama_hari(teks_lower)
        if hari:
            jumlah = sch.hitung_jumlah_matkul(hari)
            return f"Hari {hari.capitalize()} ada {jumlah} mata kuliah."
        return "Mau tanya jumlah mata kuliah di hari apa? Sebutkan harinya ya, misal 'hari Selasa ada berapa mata kuliah?'"

    # --- Ruangan ---
    if _cocok_kata_kunci(teks_lower, KATA_KUNCI_RUANGAN):
        nama_matkul = _ekstrak_nama_matkul_dari_teks(teks_lower)
        if nama_matkul:
            ruang = sch.cari_ruangan(nama_matkul)
            if ruang:
                return f"**{nama_matkul}** diadakan di ruang **{ruang}**."
        return (
            "Mata kuliah mana yang mau kamu cari ruangannya? "
            "Coba sebutkan nama mata kuliahnya ya."
        )

    # --- Status sedang kuliah / sudah selesai ---
    if _cocok_kata_kunci(teks_lower, KATA_KUNCI_STATUS):
        return _format_status_perkuliahan()

    # --- Libur / kosong ---
    if _cocok_kata_kunci(teks_lower, KATA_KUNCI_LIBUR):
        hari = sch.normalisasi_nama_hari(teks_lower) or sch.get_hari_ini()
        jadwal = sch.get_jadwal_hari(hari)
        if not jadwal:
            return f"Betul, hari {hari.capitalize()} nggak ada jadwal kuliah. Tapi ingat, ini bukan berarti hari libur nasional ya, cuma emang nggak ada kelas aja. 😊"
        return f"Hari {hari.capitalize()} ada jadwal kuliah kok, nggak kosong. Mau lihat detailnya?"

    # --- Besok ---
    if _cocok_kata_kunci(teks_lower, KATA_KUNCI_BESOK):
        hari_besok = _hari_besok()
        if _cocok_kata_kunci(teks_lower, KATA_KUNCI_JAM):
            jadwal = sch.get_jadwal_hari(hari_besok)
            if not jadwal:
                return f"Besok ({hari_besok.capitalize()}) nggak ada jadwal kuliah."
            jadwal_terurut = sorted(jadwal, key=lambda i: i["jam_mulai"])
            pertama = jadwal_terurut[0]
            return (
                f"Besok ({hari_besok.capitalize()}) kuliah mulai jam "
                f"{pertama['jam_mulai']} WIB, yaitu {pertama['matkul']} di ruang {pertama['ruang']}."
            )
        return sch.format_jadwal_harian(hari_besok)

    # --- Hari ini ---
    if _cocok_kata_kunci(teks_lower, KATA_KUNCI_HARI_INI):
        hari_ini = sch.get_hari_ini()
        if _cocok_kata_kunci(teks_lower, KATA_KUNCI_JAM):
            jadwal = sch.get_jadwal_hari(hari_ini)
            if not jadwal:
                return f"Hari ini ({hari_ini.capitalize()}) nggak ada jadwal kuliah."
            jadwal_terurut = sorted(jadwal, key=lambda i: i["jam_mulai"])
            pertama = jadwal_terurut[0]
            return (
                f"Hari ini ({hari_ini.capitalize()}) kuliah mulai jam "
                f"{pertama['jam_mulai']} WIB, yaitu {pertama['matkul']} di ruang {pertama['ruang']}."
            )
        return sch.format_jadwal_harian(hari_ini)

    # --- Pertanyaan tentang mata kuliah spesifik (jam / jadwal) ---
    nama_matkul = _ekstrak_nama_matkul_dari_teks(teks_lower)
    if nama_matkul and ("jadwal" in teks_lower or "kapan" in teks_lower or _cocok_kata_kunci(teks_lower, KATA_KUNCI_JAM)):
        hasil = sch.cari_matkul(nama_matkul)
        if hasil:
            item = hasil[0]
            return (
                f"**{item['matkul']}** diadakan hari {item['hari'].capitalize()}, "
                f"jam {item['jam_mulai']}–{item['jam_selesai']} WIB, di ruang {item['ruang']}."
            )

    # --- Nama hari disebut tanpa kata kunci "hari ini"/"besok" ---
    hari_disebut = sch.normalisasi_nama_hari(teks_lower)
    if hari_disebut and ("kuliah" in teks_lower or "jadwal" in teks_lower or "masuk" in teks_lower):
        if _cocok_kata_kunci(teks_lower, KATA_KUNCI_JAM):
            jadwal = sch.get_jadwal_hari(hari_disebut)
            if not jadwal:
                return f"Hari {hari_disebut.capitalize()} nggak ada jadwal kuliah."
            jadwal_terurut = sorted(jadwal, key=lambda i: i["jam_mulai"])
            pertama = jadwal_terurut[0]
            return (
                f"Hari {hari_disebut.capitalize()} masuk jam {pertama['jam_mulai']} WIB "
                f"({pertama['matkul']}, ruang {pertama['ruang']})."
            )
        return sch.format_jadwal_harian(hari_disebut)

    # Tidak dikenali sebagai pertanyaan jadwal
    return None


def _format_status_perkuliahan() -> str:
    info = sch.status_perkuliahan_sekarang()
    status = info["status"]
    kelas = info["kelas"]
    hari = info["hari"].capitalize()

    if status == "libur":
        return f"Hari ini ({hari}) nggak ada jadwal kuliah sama sekali. Waktunya santai! 😄"
    if status == "sebelum_kuliah":
        return (
            f"Belum mulai kuliah nih. Kelas pertama hari ini ({hari}) adalah "
            f"{kelas['matkul']} jam {kelas['jam_mulai']} WIB di ruang {kelas['ruang']}."
        )
    if status == "sedang_kuliah":
        return (
            f"Sedang berlangsung kuliah **{kelas['matkul']}** sampai jam "
            f"{kelas['jam_selesai']} WIB di ruang {kelas['ruang']}. Semangat! 💪"
        )
    if status == "jeda":
        if kelas:
            return (
                f"Lagi jeda nih di antara kelas. Kelas berikutnya: {kelas['matkul']} "
                f"jam {kelas['jam_mulai']} WIB di ruang {kelas['ruang']}."
            )
        return "Lagi jeda di antara kelas hari ini."
    if status == "setelah_kuliah":
        return f"Semua kelas hari ini ({hari}) sudah selesai. Kerja bagus hari ini! 🎉"
    return "Belum ada info status perkuliahan saat ini."


# ---------------------------------------------------------------------
# FUNGSI UTAMA YANG DIPANGGIL OLEH app.py
# ---------------------------------------------------------------------

def generate_response(user_input: str, gemini_client: Optional[GeminiClient]) -> str:
    """
    Fungsi utama untuk menghasilkan jawaban chatbot.

    Alur:
    1. Coba jawab menggunakan data jadwal lokal (schedule.py) dahulu.
       Ini memastikan jawaban seputar jadwal SELALU akurat dan konsisten,
       sesuai database, tanpa risiko "halusinasi" dari AI.
    2. Jika tidak cocok dengan pertanyaan seputar jadwal, teruskan ke
       Gemini API (jika tersedia) untuk jawaban AI umum.
    3. Jika Gemini tidak tersedia, beri jawaban fallback yang sopan.
    """
    try:
        if not user_input or not user_input.strip():
            return "Hmm, sepertinya pertanyaannya kosong. Coba ketik pertanyaanmu ya! 😊"

        jawaban_lokal = jawab_pertanyaan_jadwal(user_input)
        if jawaban_lokal is not None:
            return jawaban_lokal

        if gemini_client is not None:
            return gemini_client.ask(user_input)

        return (
            "Maaf, pertanyaan itu di luar topik jadwal kuliah dan fitur AI umum "
            "sedang tidak tersedia. Coba tanyakan seputar jadwal kuliah Kelas F ya, "
            "misalnya 'jadwal hari ini apa?' 😊"
        )
    except Exception as exc:  # noqa: BLE001
        logger.exception("Terjadi error saat memproses pertanyaan: %s", exc)
        return (
            "Waduh, ada error saat memproses pertanyaanmu. "
            "Coba ulangi lagi atau pakai kalimat yang lebih sederhana ya 🙏"
        )
