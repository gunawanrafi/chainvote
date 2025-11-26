# Multi-Event Blockchain E-Voting (Flask)

Demo aplikasi e-voting berbasis Flask yang mendemonstrasikan konsep blockchain sederhana per-event. Setiap event menyimpan rantai blok (blockchain) di file JSON (`events.json`), sehingga tiap vote direkam sebagai block baru.

**Fitur utama**
- Simpan banyak event — setiap event punya blockchain sendiri
- Tambah kandidat dan buat event dari UI
- Lakukan voting; setiap vote menjadi satu block yang ditambahkan
- Viewer blockchain per event + pemeriksaan integritas (hash & previous_hash)

**Teknologi**
- Python 3
- Flask (web framework)
- `hashlib` (SHA-256) untuk hashing block
- HTML/CSS (+Bootstrap) untuk tampilan

**Struktur proyek (singkat)**
- `app.py` — Aplikasi Flask & logika blockchain
- `templates/` — HTML templates untuk UI
- `static/` — CSS dan aset statis (`style.css`, `uploads/`)
- `events.json` — Penyimpanan data event & blockchain
- `users.json` — (opsional) data pengguna bila ada

## Quickstart (Windows PowerShell)
1. (Opsional) Buat virtual environment dan aktifkan:
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```
2. Install dependency:
```powershell
pip install -r requirements.txt
```
3. Jalankan aplikasi:
```powershell
python app.py
```
4. Buka browser ke `http://127.0.0.1:5000`

Catatan: jika PowerShell menolak menjalankan skrip aktivasi, jalankan `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass` lalu aktifkan kembali.

## Menjalankan untuk development
- Edit `app.py` atau template di `templates/` lalu refresh browser.

## File data & keamanan
- `events.json` dan `users.json` menyimpan data lokal — perhatikan jangan commit data sensitif ke repo publik.
- Direktori `static/uploads/` berisi file yang diupload; tambahkan ke `.gitignore` agar tidak ikut ter-commit.

## Menyiapkan repository GitHub (contoh)
1. Inisialisasi repo lokal dan commit:
```powershell
git init
git add .
git commit -m "Initial commit — open-source demo e-voting"
```
2. Buat repository di GitHub lalu sambungkan remote (ganti URL):
```powershell
git branch -M main
git remote add origin https://github.com/<username>/<repo>.git
git push -u origin main
```

## Lisensi & kontribusi
- Untuk menjadikan proyek ini open-source, tambahkan file `LICENSE` (mis. MIT). Jika mau, saya bisa menambahkan `LICENSE` otomatis.
- Kontribusi: buat issue atau PR; sertakan deskripsi perubahan dan langkah untuk mereproduksi.

## Catatan pengembang
- Contoh ini bertujuan untuk edukasi/demo — jangan gunakan sistem ini untuk pemungutan suara nyata tanpa audit keamanan, enkripsi, dan validasi hukum.

Terima kasih sudah menggunakan proyek ini!
