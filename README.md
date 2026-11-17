# 🎓 FClassBot — Your Smart Class Assistant

FClassBot adalah chatbot AI interaktif untuk membantu mahasiswa **Kelas F
UIN Syarif Hidayatullah Jakarta** mendapatkan informasi jadwal kuliah
dengan cepat, mudah, dan interaktif — menggunakan Python, Streamlit, dan
Google Gemini API (free tier).

---

## 📁 Struktur Project

```
FClassBot/
├── app.py                  # Tampilan utama (UI) & alur aplikasi Streamlit
├── chatbot.py               # "Otak" chatbot: pemahaman pertanyaan + Gemini API
├── schedule.py               # Database jadwal kuliah + fungsi bantu jadwal
├── requirements.txt         # Daftar library Python yang dibutuhkan
├── .gitignore               # File/folder yang tidak diunggah ke GitHub
├── .streamlit/
│   └── secrets.toml          # Template API key (JANGAN diunggah ke GitHub)
└── README.md                 # Dokumen ini
```

### Fungsi setiap file

| File | Fungsi |
|---|---|
| `app.py` | Mengatur tampilan web (header, sidebar, chat, kartu jadwal, tabel mingguan) dan menghubungkan input pengguna ke `chatbot.py`. |
| `chatbot.py` | Memahami pertanyaan pengguna lewat pencocokan kata kunci terhadap data jadwal, lalu meneruskan ke Gemini API jika pertanyaan di luar topik jadwal. |
| `schedule.py` | Menyimpan database jadwal kuliah (dictionary Python) dan semua fungsi pencarian/pengolahan jadwal (hari ini, mingguan, status kuliah, dst). |
| `requirements.txt` | Daftar dependency: `streamlit`, `pandas`, `google-generativeai`. |
| `.streamlit/secrets.toml` | Tempat menyimpan `GEMINI_API_KEY` secara aman, tidak langsung di source code. |
| `.gitignore` | Memastikan `secrets.toml` dan file sensitif lain tidak ikut ter-commit ke GitHub. |

---

## 🚀 Panduan Menjalankan Secara Lokal

### ⚡ Cara Tercepat (Windows): Cukup Double-Click

Kalau kamu hanya ingin memakainya sendiri tanpa ribet dengan terminal,
gunakan **`start.bat`**:

1. Pastikan Python sudah terinstal (lihat langkah 1 di bawah jika belum).
2. (Opsional) isi `GEMINI_API_KEY` di `.streamlit/secrets.toml` jika ingin
   fitur AI umum aktif.
3. **Double-click file `start.bat`** di dalam folder `FClassBot`.

Pertama kali dijalankan akan sedikit lebih lama karena `start.bat`
otomatis membuat virtual environment dan menginstal semua library yang
dibutuhkan. Setelah itu, aplikasi langsung terbuka di browser.

Di hari-hari berikutnya, kamu tinggal **double-click `start.bat` lagi** —
tidak perlu mengetik perintah apa pun, karena venv dan library sudah
tersimpan dan langsung dipakai ulang.

Untuk menghentikan aplikasi, cukup tutup jendela hitam (terminal) yang
muncul, atau tekan `CTRL+C` di dalamnya.

> Bagian di bawah ini (langkah 1–5) menjelaskan apa yang sebenarnya
> dilakukan `start.bat` secara manual, kalau suatu saat kamu ingin
> memahami atau menjalankannya sendiri lewat terminal.

### 1. Instal Python

Unduh dan instal Python 3.10 atau lebih baru dari situs resmi:
👉 https://www.python.org/downloads/

Saat instalasi di Windows, centang opsi **"Add Python to PATH"**.

Cek instalasi berhasil dengan:

```bash
python --version
```

### 2. Buat Virtual Environment (disarankan)

```bash
# Masuk ke folder project
cd FClassBot

# Buat virtual environment
python -m venv venv

# Aktifkan virtual environment
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate
```

### 3. Instal Library yang Dibutuhkan

```bash
pip install -r requirements.txt
```

### 4. Siapkan API Key Gemini (Opsional tapi Disarankan)

1. Buka https://aistudio.google.com/app/apikey
2. Login dengan akun Google, lalu klik **"Create API Key"** (gratis / free tier).
3. Salin API key yang didapat.
4. Buka file `.streamlit/secrets.toml`, lalu ganti isinya:

```toml
GEMINI_API_KEY = "tempel_api_key_asli_kamu_di_sini"
```

> ⚠️ **Jangan pernah mengunggah file `secrets.toml` ke GitHub.** File ini
> sudah otomatis diabaikan oleh `.gitignore`.

Jika API key tidak diisi, FClassBot **tetap bisa digunakan** untuk semua
pertanyaan seputar jadwal kuliah — hanya fitur "AI umum" (pertanyaan di
luar topik jadwal) yang tidak aktif.

### 5. Jalankan Aplikasi

```bash
streamlit run app.py
```

Aplikasi akan terbuka otomatis di browser pada alamat:
`http://localhost:8501`

---

## ☁️ Panduan Deployment Gratis ke Streamlit Community Cloud

### 1. Buat Repository GitHub

1. Buka https://github.com dan login/daftar akun.
2. Klik **"New repository"**.
3. Beri nama, misalnya `fclassbot`.
4. Pilih **Public** (diperlukan untuk Streamlit Community Cloud free tier), lalu klik **Create repository**.

### 2. Unggah Project ke GitHub

Di folder project (`FClassBot/`), jalankan:

```bash
git init
git add .
git commit -m "Initial commit - FClassBot"
git branch -M main
git remote add origin https://github.com/USERNAME_KAMU/fclassbot.git
git push -u origin main
```

> Karena `secrets.toml` sudah ada di `.gitignore`, file tersebut **tidak**
> akan ikut terunggah — aman dari kebocoran API key.

### 3. Hubungkan GitHub dengan Streamlit Community Cloud

1. Buka https://share.streamlit.io/ dan login menggunakan akun GitHub.
2. Klik **"New app"**.
3. Pilih repository `fclassbot`, branch `main`, dan file utama `app.py`.
4. Klik **"Deploy!"**.

### 4. Masukkan API Key ke Bagian Secrets

1. Di halaman aplikasi pada dashboard Streamlit Community Cloud, klik **"⋮" (menu titik tiga)** → **"Settings"** → **"Secrets"**.
2. Tempelkan isi berikut (dengan API key asli kamu):

```toml
GEMINI_API_KEY = "api_key_asli_kamu"
```

3. Klik **Save**. Aplikasi akan otomatis restart dengan API key yang baru.

### 5. Dapatkan URL Website FClassBot

Setelah deployment selesai, Streamlit akan memberikan URL publik, biasanya
dengan format:

```
https://fclassbot-xxxxx.streamlit.app
```

URL ini bisa dibagikan ke seluruh mahasiswa Kelas F dan diakses langsung
dari browser tanpa perlu menginstal Python apa pun.

---

## 🛠️ Penanganan Error

- **Gemini API tidak tersedia / API key salah** → FClassBot otomatis
  memberi tahu pengguna dan tetap menjawab pertanyaan seputar jadwal
  menggunakan data lokal.
- **Library `google-generativeai` belum terpasang** → aplikasi tetap
  berjalan normal; fitur AI umum otomatis nonaktif.
- **Input kosong** → chatbot akan meminta pengguna mengetik ulang
  pertanyaannya.
- **Kesalahan tak terduga saat memproses pesan** → ditangani dengan
  try/except di `chatbot.py` sehingga aplikasi tidak crash, dan pengguna
  mendapat pesan error yang ramah.

---

## 💡 Catatan Biaya

Seluruh komponen pada FClassBot menggunakan layanan **gratis**:

- **Streamlit Community Cloud** — hosting gratis untuk aplikasi publik.
- **Google Gemini API** — free tier dengan model `gemini-1.5-flash`.
- **GitHub** — repository publik gratis.

Dengan begitu, FClassBot dapat dioperasikan oleh seluruh mahasiswa Kelas F
tanpa biaya operasional tambahan.

---

Dibuat dengan 💙 untuk Kelas F — UIN Syarif Hidayatullah Jakarta.
