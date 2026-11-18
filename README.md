# Veritas Review

Aplikasi web untuk memeriksa pola teks pada **satu dokumen PDF atau Word `.docx`**. Aplikasi menampilkan skor indikasi, jumlah kata, jumlah halaman PDF, rincian indikator, dan riwayat pemeriksaan.

> **Penting:** skor adalah hasil aturan sederhana, bukan bukti bahwa seseorang menggunakan AI. Versi sekarang tidak memiliki login dan hanya ditujukan untuk demonstrasi di komputer sendiri. Jangan membuka aplikasi ini ke internet atau mengunggah dokumen sensitif.

## Cara paling mudah membuka web (Windows + Docker Desktop)

Ikuti urutan ini untuk menjalankan aplikasi pertama kali.

### 1. Pasang dan nyalakan Docker Desktop

Jika Docker Desktop belum terpasang, pasang Docker Desktop untuk Windows terlebih dahulu. Docker Desktop dapat memerlukan WSL 2; ikuti petunjuk pemasangan resminya bila diminta.

Setelah terpasang:

1. Buka **Docker Desktop** dari menu Start.
2. Tunggu sampai aplikasi menunjukkan bahwa Docker Engine sedang berjalan (**Engine running** atau **Docker is running**). Membuka terminal saja belum menyalakan Docker Engine.
3. Biarkan Docker Desktop tetap berjalan.

Periksa status Docker di PowerShell:

```powershell
docker info
```

Jika bagian **Server** menampilkan informasi dan tidak ada error, lanjutkan. Jika muncul `failed to connect to the docker API` atau `The system cannot find the file specified`, Docker Desktop/Engine belum berjalan. Buka Docker Desktop, tunggu sampai siap, lalu coba lagi.

### 2. Buka folder proyek di PowerShell

Buka PowerShell di VS Code (**Terminal → New Terminal**), lalu pindah ke folder proyek:

```powershell
cd "D:\Samsul Akmal\Pemograman\ML\detektor pdf v1.0"
```

Pastikan terminal berada di folder yang berisi `compose.yaml`:

```powershell
Get-ChildItem compose.yaml
```

### 3. Buat konfigurasi lokal

Jika file `.env` belum ada, buat salinannya dari contoh:

```powershell
if (-not (Test-Path .env)) { Copy-Item .env.example .env }
notepad .env
```

Ubah `POSTGRES_PASSWORD` menjadi kata sandi lokal database. Secara default, pgAdmin memakai email `admin@example.com` dan password database tersebut untuk login. Jika ingin password pgAdmin berbeda, isi juga `PGADMIN_DEFAULT_EMAIL` dan `PGADMIN_DEFAULT_PASSWORD`. Jangan kirim atau unggah file `.env`; file ini berisi kata sandi dan memang tidak disertakan ke Git.

Anda hanya perlu membuat `.env` sekali. Jika file itu sudah ada, jangan menyalinnya lagi karena isi lokal bisa tertimpa.

### 4. Jalankan aplikasi

Di terminal PowerShell yang sama:

```powershell
docker compose up --build
```

Pada penggunaan pertama, Docker mungkin perlu mengunduh image dan memasang dependensi, sehingga prosesnya dapat memerlukan beberapa menit. Tunggu sampai log menunjukkan Streamlit berjalan di port `8501`. **Jangan tutup terminal ini** selama ingin memakai web.

### 5. Buka tampilan web

Buka browser seperti Edge atau Chrome dan masukkan alamat ini:

**http://localhost:8501**

Alamat tersebut hanya dapat dibuka dari komputer yang sedang menjalankan aplikasi. Tidak ada halaman login pada versi ini. Pilih tab **Analisis dokumen**, unggah satu PDF atau Word `.docx`, lalu tekan **Analisis dokumen**. Untuk PDF hasil scan tanpa teks digital, aplikasi belum mendukung OCR. File `.doc` lama perlu disimpan ulang sebagai `.docx`.

### 5a. Melihat isi database melalui web

1. Di bagian atas halaman, pilih tab **Database**.
2. Halaman menunjukkan nama database, versi server PostgreSQL, status pgvector, dan jumlah baris dalam tabel `analysis_records`.
3. Tabel menampilkan ID pemeriksaan, waktu dibuat, format dokumen, skor, jumlah halaman, dan jumlah kata.
4. Pilih ID pemeriksaan di bawah tabel untuk melihat JSON kolom `findings` (rincian angka indikator).

Jika tabel kosong, buka tab **Analisis dokumen**, unggah dokumen, lalu tekan **Analisis dokumen** terlebih dahulu. Tab **Riwayat** adalah ringkasan; tab **Database** menampilkan ID lengkap dan rincian record yang tersimpan.

pgvector berstatus aktif berarti ekstensi tersedia di PostgreSQL. Versi aplikasi ini belum menyimpan embeddings/vektor.

### 5b. Mengelola database dengan pgAdmin

pgAdmin adalah antarmuka web untuk PostgreSQL, seperti phpMyAdmin untuk MySQL.

1. Buka **http://localhost:5050**.
2. Login dengan `PGADMIN_DEFAULT_EMAIL` dan `PGADMIN_DEFAULT_PASSWORD` dari `.env`. Jika belum diatur, gunakan `admin@example.com` dan nilai `POSTGRES_PASSWORD`.
3. Klik **Add New Server**. Pada tab **General**, isi nama, misalnya `Veritas lokal`.
4. Pada tab **Connection**, isi:
   - **Host name/address:** `db`
   - **Port:** `5432`
   - **Maintenance database:** nilai `POSTGRES_DB` (default `review_db`)
   - **Username:** nilai `POSTGRES_USER` (default `review_app`)
   - **Password:** nilai `POSTGRES_PASSWORD`
5. Simpan. Buka **Servers → Veritas lokal → Databases → [database dari POSTGRES_DB] → Schemas → public → Tables → analysis_records**, lalu klik kanan tabel dan pilih **View/Edit Data → All Rows**.

pgAdmin hanya diikat ke komputer ini (`127.0.0.1`); jangan ubah pengaturan port agar dapat diakses dari internet. Untuk penggunaan sehari-hari, atur password pgAdmin terpisah dari password database.

### 6. Hentikan atau jalankan kembali

- Jika aplikasi berjalan di terminal, tekan **Ctrl+C** untuk menghentikannya.
- Untuk memulai lagi setelah Docker Desktop siap:

  ```powershell
  docker compose up
  ```

- Jika ingin aplikasi berjalan di latar tanpa terminal yang terus menampilkan log:

  ```powershell
  docker compose up -d
  ```

  Buka `http://localhost:8501` untuk aplikasi atau `http://localhost:5050` untuk pgAdmin, lalu lihat log dengan `docker compose logs -f app`. Untuk menghentikan layanan latar:

  ```powershell
  docker compose down
  ```

Perintah `docker compose down` menghentikan kontainer tetapi **tidak menghapus riwayat database**.

## Jika gagal dibuka

### Pesan `failed to connect to the docker API`

Docker Engine belum aktif. Buka Docker Desktop, tunggu sampai statusnya siap, kemudian jalankan:

```powershell
docker info
docker compose up --build
```

### Browser menunjukkan `This site can't be reached`

Pastikan terminal masih menjalankan layanan dan periksa statusnya:

```powershell
docker compose ps
docker compose logs --tail 100 app
```

Jika service aplikasi tidak berstatus `Up`, kirim pesan error dari log tersebut (jangan kirim isi `.env`). Pastikan juga alamat yang dibuka tepat `http://localhost:8501`.

### Port 8501 sudah digunakan

Hentikan aplikasi lain yang menggunakan port tersebut, lalu coba lagi. Jangan membuka port aplikasi ke jaringan publik; konfigurasi ini sengaja hanya mengikat alamat lokal `127.0.0.1`.

### Docker meminta login atau tidak dapat mengunduh image

Pastikan koneksi internet tersedia dan Docker Desktop sudah siap. Jika jaringan kampus/perusahaan memakai proxy, ikuti pengaturan proxy Docker Desktop dari administrator jaringan.

## Lokasi dan penghapusan data

Database PostgreSQL 16 dengan ekstensi pgvector berjalan di kontainer dan datanya disimpan persisten pada volume Docker bernama `postgres_data`. Data tetap ada setelah Docker dihentikan atau kontainer dimulai ulang.

Ekstensi pgvector diaktifkan oleh migrasi Alembic (`CREATE EXTENSION IF NOT EXISTS vector`). Pada versi sekarang, ekstensi tersebut **belum dipakai untuk menyimpan embeddings atau mencari kemiripan**. Mesin deteksi tetap menggunakan aturan karakter, frasa, panjang kalimat, dan daftar berpoin seperti spesifikasi awal.

Yang disimpan untuk setiap pemeriksaan:

- ID dan waktu pemeriksaan;
- format file (`PDF` atau `DOCX`);
- skor, jumlah kata, dan jumlah halaman jika tersedia;
- nilai indikator dan jumlah temuan.

Yang **tidak** disimpan oleh aplikasi:

- file PDF/DOCX dan nama file;
- teks yang diekstrak dari dokumen;
- metadata sumber dokumen.

Untuk menghapus kontainer tetapi mempertahankan riwayat:

```powershell
docker compose down
```

Untuk menghapus seluruh riwayat database demo secara permanen:

```powershell
docker compose down -v
```

Perintah kedua tidak dapat dibatalkan. Gunakan hanya jika memang ingin menghapus data demo.

## Apa yang dijalankan Docker

`docker compose up --build` akan:

1. menjalankan PostgreSQL 16 berisi ekstensi pgvector pada jaringan internal Docker;
2. menjalankan pgAdmin pada `localhost:5050` untuk mengelola PostgreSQL lewat browser;
3. membangun lingkungan Python dari `requirements.txt`;
4. menunggu database siap;
5. menjalankan migrasi Alembic untuk membuat tabel riwayat dan mengaktifkan ekstensi pgvector;
6. menjalankan Streamlit dan menyediakan web pada `localhost:8501`.

Batas ukuran unggahan adalah 20 MB. File diolah sementara oleh aplikasi dan tidak disimpan ke disk oleh kode aplikasi.

## Struktur proyek

| Berkas/folder | Fungsi |
|---|---|
| `app.py` | Antarmuka Streamlit, alur unggah, riwayat, dan tampilan database. |
| `detector.py` | Ekstraksi teks PDF/DOCX dan perhitungan indikator. |
| `database.py` | Model SQLAlchemy, koneksi PostgreSQL, penyimpanan dan pembacaan ringkasan. |
| `migrations/` | Migrasi skema database dengan Alembic. |
| `compose.yaml` | Definisi layanan aplikasi dan PostgreSQL. |
| `Dockerfile` | Cara membangun image aplikasi. |
| `.env.example` | Contoh konfigurasi lokal; salin menjadi `.env`. |
| `.vscode/settings.json` | Pengaturan opsional untuk VS Code; tidak diperlukan untuk menjalankan aplikasi. |
| `laporan_tugas.md` | Laporan tugas proyek. |

Folder `__pycache__/` dibuat otomatis oleh Python dan tidak dibutuhkan untuk menjalankan aplikasi. Folder tersebut diabaikan oleh Git dan Docker.

## Menjalankan tanpa Docker (opsi lanjutan)

Opsi ini hanya cocok jika Python dan PostgreSQL sudah disiapkan sendiri. Anda harus membuat database dan pengguna PostgreSQL terlebih dahulu. Setelah itu, dari PowerShell pada folder proyek:

```powershell
python -m pip install -r requirements.txt
$env:DATABASE_URL = "postgresql+psycopg://NAMA_PENGGUNA:KATA_SANDI@localhost:5432/NAMA_DATABASE"
alembic upgrade head
python -m streamlit run app.py
```

Ganti nilai contoh pada URL dengan kredensial database Anda. Kata sandi yang berisi karakter khusus perlu di-URL-encode. Jangan menyimpan URL berkredensial ke Git. Setelah perintah Streamlit berjalan, buka alamat lokal yang dicetak di terminal (umumnya `http://localhost:8501`).

## Batas penggunaan saat ini

Aplikasi ini adalah fondasi demo lokal, **belum merupakan produk perusahaan yang siap dipublikasikan atau dijual untuk penggunaan langsung**. Belum tersedia login, peran admin/dosen, pemisahan data antar pengguna/institusi, HTTPS, audit tindakan pengguna, pencadangan terjadwal, atau prosedur retensi hasil. Riwayat yang tersimpan di PostgreSQL bersifat bersama dan versi ini tidak mengidentifikasi dosen yang menjalankan pemeriksaan.

Jangan mengubah port agar terbuka ke jaringan atau internet sebelum menambahkan autentikasi dan otorisasi, perlindungan koneksi, kebijakan data, backup/restore, penghapusan riwayat, serta uji keamanan dan beban. Pengaturan koneksi database hanyalah titik awal untuk demo; kapasitas 20 pengguna harus diuji pada server tujuan sebelum dijanjikan.
