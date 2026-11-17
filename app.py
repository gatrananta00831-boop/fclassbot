"""
app.py
------
Entry point aplikasi Streamlit untuk FClassBot – AI Interactive Class
Assistant untuk Mahasiswa Kelas F UIN Syarif Hidayatullah Jakarta.

Menjalankan aplikasi secara lokal:
    streamlit run app.py

File ini HANYA bertanggung jawab atas tampilan (UI) dan alur interaksi.
Logika pemahaman pertanyaan ada di chatbot.py, dan data jadwal ada di
schedule.py.
"""

from __future__ import annotations

import os

import streamlit as st

import schedule as sch
from chatbot import GeminiClient, generate_response

# =======================================================================
# KONFIGURASI HALAMAN
# =======================================================================

st.set_page_config(
    page_title="FClassBot - Your Smart Class Assistant",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded",
)

# =======================================================================
# CSS KUSTOM — Tema Biru Navy, Putih, Biru Muda
# =======================================================================

CUSTOM_CSS = """
<style>
:root {
    --navy: #0A1F44;
    --navy-light: #16305C;
    --blue: #3A7BD5;
    --blue-light: #EAF2FF;
    --white: #FFFFFF;
}

.stApp {
    background-color: var(--blue-light);
}

/* Header */
.fcb-header {
    background: linear-gradient(135deg, var(--navy) 0%, var(--blue) 100%);
    padding: 1.6rem 2rem;
    border-radius: 16px;
    margin-bottom: 1.2rem;
    box-shadow: 0 4px 14px rgba(10, 31, 68, 0.25);
}
.fcb-header h1 {
    color: var(--white);
    margin: 0;
    font-size: 2rem;
    font-weight: 800;
    display: flex;
    align-items: center;
    gap: 0.5rem;
}
.fcb-header p {
    color: #DCE8FF;
    margin: 0.3rem 0 0 0;
    font-size: 1rem;
}

/* Cards */
.fcb-card {
    background-color: var(--white);
    border-radius: 14px;
    padding: 1.2rem 1.4rem;
    box-shadow: 0 2px 10px rgba(10, 31, 68, 0.08);
    border: 1px solid #E3ECFC;
    margin-bottom: 1rem;
}
.fcb-card h3 {
    color: var(--navy);
    margin-top: 0;
}

/* Sidebar */
section[data-testid="stSidebar"] {
    background-color: var(--navy);
}
section[data-testid="stSidebar"] * {
    color: var(--white) !important;
}
section[data-testid="stSidebar"] .stRadio label {
    font-size: 1.02rem;
}

/* Chat bubbles */
.stChatMessage {
    border-radius: 14px;
}

/* Buttons */
.stButton button {
    background-color: var(--blue);
    color: var(--white);
    border-radius: 10px;
    border: none;
    font-weight: 600;
    transition: all 0.15s ease-in-out;
}
.stButton button:hover {
    background-color: var(--navy);
    color: var(--white);
}

/* Table */
table {
    background-color: var(--white);
}
</style>
"""

st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

# =======================================================================
# INISIALISASI GEMINI CLIENT (DENGAN FALLBACK AMAN)
# =======================================================================


@st.cache_resource(show_spinner=False)
def get_gemini_client() -> GeminiClient:
    """
    Mengambil API key dari Streamlit Secrets terlebih dahulu, lalu dari
    environment variable sebagai cadangan. Di-cache agar tidak membuat
    koneksi baru setiap kali pengguna mengirim pesan.
    """
    api_key = None
    try:
        api_key = st.secrets.get("GEMINI_API_KEY")
    except Exception:  # noqa: BLE001
        api_key = None

    if not api_key:
        api_key = os.environ.get("GEMINI_API_KEY")

    return GeminiClient(api_key)


gemini_client = get_gemini_client()

# =======================================================================
# STATE SESSION
# =======================================================================

if "messages" not in st.session_state:
    st.session_state.messages = [
        {
            "role": "assistant",
            "content": (
                "Halo! 👋 Aku **FClassBot**, asisten kelas untuk Kelas F "
                "UIN Syarif Hidayatullah Jakarta. Tanya aku soal jadwal kuliah, "
                "ruangan, atau hal lainnya ya!"
            ),
        }
    ]

if "menu" not in st.session_state:
    st.session_state.menu = "Chat Assistant"

if "pending_quick_question" not in st.session_state:
    st.session_state.pending_quick_question = None


# =======================================================================
# SIDEBAR
# =======================================================================

with st.sidebar:
    st.markdown("## 🎓 FClassBot")
    st.caption("Your Smart Class Assistant")
    st.markdown("---")

    menu = st.radio(
        "Menu",
        ["Home", "Chat Assistant", "Class Schedule", "About FClassBot"],
        index=["Home", "Chat Assistant", "Class Schedule", "About FClassBot"].index(
            st.session_state.menu
        ),
        label_visibility="collapsed",
    )
    st.session_state.menu = menu

    st.markdown("---")
    if gemini_client.enabled:
        st.success("AI umum: Aktif ✅")
    else:
        st.warning("AI umum: Nonaktif ⚠️\n(Jadwal tetap berfungsi normal)")

    st.markdown("---")
    if st.button("🗑️ Hapus Percakapan", use_container_width=True):
        st.session_state.messages = [
            {
                "role": "assistant",
                "content": "Riwayat percakapan sudah dihapus. Ada yang bisa aku bantu lagi?",
            }
        ]
        st.rerun()


# =======================================================================
# KOMPONEN BANTU UI
# =======================================================================


def render_header():
    st.markdown(
        """
        <div class="fcb-header">
            <h1>🎓 FClassBot</h1>
            <p>Your Smart Class Assistant — Kelas F UIN Syarif Hidayatullah Jakarta</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_kartu_jadwal_hari_ini():
    hari_ini = sch.get_hari_ini()
    jadwal = sch.get_jadwal_hari(hari_ini)
    status_info = sch.status_perkuliahan_sekarang()

    st.markdown('<div class="fcb-card">', unsafe_allow_html=True)
    st.markdown(f"### 📅 Jadwal Hari Ini — {hari_ini.capitalize()}")

    if not jadwal:
        st.info("Tidak ada jadwal kuliah hari ini.")
    else:
        for item in jadwal:
            st.markdown(
                f"- **{item['matkul']}**  \n"
                f"  🕐 {item['jam_mulai']}–{item['jam_selesai']} WIB &nbsp;|&nbsp; 🏫 Ruang {item['ruang']}"
            )

    status_text = {
        "libur": "Tidak ada kuliah hari ini.",
        "sebelum_kuliah": "Belum mulai kuliah hari ini.",
        "sedang_kuliah": "Sedang berlangsung kuliah sekarang.",
        "jeda": "Sedang jeda di antara kelas.",
        "setelah_kuliah": "Semua kelas hari ini sudah selesai.",
    }.get(status_info["status"], "")
    if status_text:
        st.caption(f"ℹ️ Status: {status_text}")

    st.markdown("</div>", unsafe_allow_html=True)


def render_tabel_jadwal_mingguan():
    st.markdown('<div class="fcb-card">', unsafe_allow_html=True)
    st.markdown("### 📋 Jadwal Kuliah Mingguan")

    rows = []
    for hari in sch.HARI_URUTAN:
        daftar = sch.get_jadwal_hari(hari)
        if not daftar:
            rows.append(
                {
                    "Hari": hari.capitalize(),
                    "Mata Kuliah": "-",
                    "Jam": "-",
                    "Ruang": "-",
                }
            )
        else:
            for item in daftar:
                rows.append(
                    {
                        "Hari": hari.capitalize(),
                        "Mata Kuliah": item["matkul"],
                        "Jam": f"{item['jam_mulai']}–{item['jam_selesai']} WIB",
                        "Ruang": item["ruang"],
                    }
                )

    try:
        import pandas as pd

        df = pd.DataFrame(rows)
        st.dataframe(df, use_container_width=True, hide_index=True)
    except ImportError:  # pragma: no cover
        st.table(rows)

    st.markdown("</div>", unsafe_allow_html=True)


def kirim_pesan_dan_jawab(teks: str):
    st.session_state.messages.append({"role": "user", "content": teks})
    jawaban = generate_response(teks, gemini_client)
    st.session_state.messages.append({"role": "assistant", "content": jawaban})


# =======================================================================
# HALAMAN: HOME
# =======================================================================

if st.session_state.menu == "Home":
    render_header()

    col1, col2 = st.columns([1, 1])
    with col1:
        render_kartu_jadwal_hari_ini()
    with col2:
        st.markdown('<div class="fcb-card">', unsafe_allow_html=True)
        st.markdown("### 👋 Selamat Datang!")
        st.write(
            "FClassBot membantu kamu, mahasiswa **Kelas F UIN Syarif "
            "Hidayatullah Jakarta**, untuk mendapatkan informasi jadwal "
            "kuliah dengan cepat dan interaktif."
        )
        st.write("Gunakan menu **Chat Assistant** untuk mulai bertanya, atau cek **Class Schedule** untuk melihat jadwal lengkap.")
        if st.button("💬 Mulai Chat Sekarang", use_container_width=True):
            st.session_state.menu = "Chat Assistant"
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

    render_tabel_jadwal_mingguan()


# =======================================================================
# HALAMAN: CHAT ASSISTANT
# =======================================================================

elif st.session_state.menu == "Chat Assistant":
    render_header()

    st.markdown("#### ⚡ Quick Questions")
    qcols = st.columns(5)
    quick_questions = [
        ("📅 Jadwal Hari Ini", "Hari ini ada kuliah apa?"),
        ("📋 Jadwal Mingguan", "Tampilkan jadwal mingguan"),
        ("🔍 Cari Mata Kuliah", "__CARI_MATKUL__"),
        ("🏫 Cari Ruangan", "__CARI_RUANGAN__"),
        ("❓ Bantuan FClassBot", "Bantuan"),
    ]
    for col, (label, payload) in zip(qcols, quick_questions):
        if col.button(label, use_container_width=True, key=f"qq_{label}"):
            st.session_state.pending_quick_question = payload

    # Tangani quick question yang butuh input tambahan (cari matkul/ruangan)
    if st.session_state.pending_quick_question == "__CARI_MATKUL__":
        with st.form("form_cari_matkul", clear_on_submit=True):
            nama = st.text_input("Masukkan nama mata kuliah yang ingin dicari:")
            submitted = st.form_submit_button("Cari")
        if submitted and nama.strip():
            kirim_pesan_dan_jawab(f"Kapan jadwal {nama}?")
            st.session_state.pending_quick_question = None
            st.rerun()

    elif st.session_state.pending_quick_question == "__CARI_RUANGAN__":
        with st.form("form_cari_ruangan", clear_on_submit=True):
            nama = st.text_input("Masukkan nama mata kuliah untuk cek ruangannya:")
            submitted = st.form_submit_button("Cari Ruangan")
        if submitted and nama.strip():
            kirim_pesan_dan_jawab(f"{nama} ruangannya di mana?")
            st.session_state.pending_quick_question = None
            st.rerun()

    elif st.session_state.pending_quick_question:
        teks = st.session_state.pending_quick_question
        st.session_state.pending_quick_question = None
        kirim_pesan_dan_jawab(teks)
        st.rerun()

    st.markdown("---")

    # Riwayat percakapan
    chat_container = st.container()
    with chat_container:
        for msg in st.session_state.messages:
            avatar = "🎓" if msg["role"] == "assistant" else "🧑‍🎓"
            with st.chat_message(msg["role"], avatar=avatar):
                st.markdown(msg["content"])

    # Input chat
    user_input = st.chat_input("Tulis pertanyaanmu di sini... (misal: 'besok kuliah jam berapa?')")
    if user_input:
        kirim_pesan_dan_jawab(user_input)
        st.rerun()


# =======================================================================
# HALAMAN: CLASS SCHEDULE
# =======================================================================

elif st.session_state.menu == "Class Schedule":
    render_header()
    render_kartu_jadwal_hari_ini()
    render_tabel_jadwal_mingguan()

    st.markdown('<div class="fcb-card">', unsafe_allow_html=True)
    st.markdown("### 🔍 Cari Mata Kuliah / Ruangan")
    keyword = st.text_input("Ketik nama mata kuliah:")
    if keyword.strip():
        hasil = sch.cari_matkul(keyword)
        if hasil:
            for item in hasil:
                st.markdown(
                    f"- **{item['matkul']}** — {item['hari'].capitalize()}, "
                    f"{item['jam_mulai']}–{item['jam_selesai']} WIB, Ruang {item['ruang']}"
                )
        else:
            st.warning("Mata kuliah tidak ditemukan dalam database jadwal.")
    st.markdown("</div>", unsafe_allow_html=True)


# =======================================================================
# HALAMAN: ABOUT FCLASSBOT
# =======================================================================

elif st.session_state.menu == "About FClassBot":
    render_header()

    st.markdown('<div class="fcb-card">', unsafe_allow_html=True)
    st.markdown("### ℹ️ Tentang FClassBot")
    st.write(
        """
        **FClassBot** adalah asisten kelas berbasis AI yang dirancang khusus
        untuk membantu mahasiswa **Kelas F UIN Syarif Hidayatullah Jakarta**
        memperoleh informasi perkuliahan dengan cepat, mudah, dan interaktif.

        **Fitur utama:**
        - Chat interaktif dalam bahasa Indonesia sehari-hari
        - Informasi jadwal kuliah harian & mingguan
        - Pencarian mata kuliah dan ruangan kelas
        - Deteksi status perkuliahan (sebelum / sedang / setelah kuliah)
        - Tetap berfungsi untuk jadwal walau API AI sedang tidak tersedia

        **Teknologi:**
        - Python & Streamlit
        - Google Gemini API (free tier)
        - Data jadwal lokal (Python dictionary)

        Dibuat dengan 💙 untuk Kelas F.
        """
    )
    st.markdown("</div>", unsafe_allow_html=True)
