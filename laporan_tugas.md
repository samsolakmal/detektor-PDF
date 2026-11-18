# Laporan Tugas

## Aplikasi Deteksi Jejak Tulisan AI pada Dokumen PDF dan Word

### 1. Ringkasan Proyek

Proyek ini merupakan aplikasi web berbasis Streamlit untuk memeriksa pola tekstual pada satu dokumen PDF atau Word `.docx`. Aplikasi mengekstrak teks, menghitung empat indikator rule-based, menampilkan ringkasan hasil, menyediakan tab Database untuk melihat baris tersimpan, dan menyimpan riwayat pemeriksaan ke PostgreSQL.

Ekstensi **pgvector** dipasang dan diaktifkan di PostgreSQL sesuai kebutuhan tugas. Sesuai spesifikasi deteksi awal, aplikasi **belum membuat embeddings, belum menyimpan vector, dan belum melakukan pencarian kemiripan**. Dengan demikian, pgvector saat ini merupakan ekstensi database yang siap digunakan untuk pengembangan terpisah di masa depan, bukan bagian dari perhitungan skor saat ini.

Skor adalah indikasi berdasarkan pola yang ditemukan. Skor tidak membuktikan bahwa mahasiswa menggunakan AI dan tidak boleh menjadi satu-satunya dasar keputusan akademik.

### 2. Tujuan

- Menerima satu file PDF atau Word `.docx`.
- Mengekstrak teks, metadata PDF, serta teks dasar dari dokumen Word.
- Menilai empat kelompok pola forensik teks dengan batas total 100 poin.
- Menyimpan riwayat hasil ringkas tanpa menyimpan file atau teks mahasiswa.
- Mengaktifkan ekstensi pgvector pada layanan PostgreSQL.
- Memisahkan antarmuka, mesin analisis, dan akses database agar kode mudah dipahami.

### 3. Teknologi

| Teknologi | Penggunaan |
|---|---|
| Python | Bahasa pemrograman aplikasi. |
| Streamlit | Antarmuka web dan dashboard. |
| `pypdf` | Membaca teks, jumlah halaman, dan metadata `/Creator` serta `/Producer` dari PDF. |
| `python-docx` | Membaca paragraf, tabel, header/footer, dan metadata penulis dari `.docx`. |
| `re`, `statistics` | Pencocokan pola dan perhitungan standar deviasi kalimat. |
| PostgreSQL 16 + pgvector | Penyimpanan riwayat; ekstensi `vector` diaktifkan, tetapi embeddings tidak digunakan. |
| SQLAlchemy + psycopg | Model data dan koneksi Python ke PostgreSQL. |
| Alembic | Migrasi skema dan aktivasi ekstensi database secara berurutan. |
| Docker Compose | Menjalankan aplikasi dan PostgreSQL pada demo lokal. |
| `unittest` | Pengujian ekstraksi, perhitungan, penyimpanan, dan perlindungan privasi. |

### 4. Struktur Folder dan File

```text
detektor pdf v1.0/
├── app.py                                  # Antarmuka web Streamlit
├── detector.py                             # Ekstraksi dokumen dan mesin skor
├── database.py                             # Model serta akses PostgreSQL
├── requirements.txt                        # Dependensi Python
├── Dockerfile                              # Cara membuat image aplikasi
├── compose.yaml                            # Layanan aplikasi + PostgreSQL/pgvector
├── alembic.ini                             # Konfigurasi migrasi database
├── .env.example                            # Contoh variabel lingkungan
├── .env                                    # Rahasia lokal; jangan dibagikan/di-commit
├── .vscode/settings.json                   # Pengaturan opsional untuk VS Code
├── .gitignore                              # File lokal/cache yang tidak dilacak Git
├── .dockerignore                           # File yang tidak dimasukkan ke image
├── README.md                               # Panduan instalasi dan penggunaan
├── laporan_tugas.md                        # Laporan proyek ini
├── migrations/
│   ├── env.py                              # Penghubung Alembic ke database
│   ├── script.py.mako                      # Template pembuatan migrasi
│   └── versions/
│       ├── 20261112_0001_create_analysis_records.py
│       └── 20261112_0002_enable_pgvector.py
└── tests/
    ├── test_detector.py                    # Tes ekstraksi dan skor
    └── test_database.py                    # Tes penyimpanan riwayat/privasi
```

Folder `__pycache__/` yang mungkin muncul ketika Python berjalan hanya berisi cache bytecode otomatis. Folder itu tidak dibutuhkan untuk menjalankan aplikasi dan sudah dikecualikan melalui `.gitignore` dan `.dockerignore`; folder dapat dibuat kembali otomatis oleh Python.

#### Penjelasan fungsi setiap file

| File/folder | Fungsi dan alasan dibutuhkan |
|---|---|
| `app.py` | Menggambar dashboard, menerima unggahan, memanggil ekstraksi dan skor, menyimpan hasil, serta menampilkan riwayat dan data database. |
| `detector.py` | Mengisolasi kode ekstraksi PDF/DOCX dan empat aturan analisis dari kode tampilan. |
| `database.py` | Mengatur koneksi, tabel SQLAlchemy, penyimpanan ringkasan, dan pembacaan riwayat. |
| `migrations/` | Menyimpan perubahan skema sebagai riwayat yang bisa diterapkan berurutan dan diulang di lingkungan lain. |
| `compose.yaml` | Menyediakan image `pgvector/pgvector:pg16`, PostgreSQL, volume persisten, health check, dan aplikasi. |
| `Dockerfile` | Memasang dependensi, menyalin kode aplikasi, menerapkan migrasi, lalu menjalankan Streamlit. |
| `.env.example` | Contoh konfigurasi. Salin menjadi `.env` lokal dan ganti kata sandi sebelum penggunaan. |
| `.vscode/settings.json` | Pengaturan editor VS Code untuk membaca file lingkungan; tidak dibutuhkan oleh aplikasi atau image Docker. |
| `README.md` | Petunjuk rinci menginstal, membuka, menghentikan, dan menangani kendala aplikasi. |
| `tests/` | Pengujian otomatis untuk menjaga perilaku tetap benar saat kode dikembangkan. |

File-file tersebut memiliki fungsi aplikasi, database, migrasi, dokumentasi, atau pengujian. `.vscode/settings.json` opsional untuk pengembangan di VS Code dan tidak ikut dimasukkan ke image. Cache `__pycache__` tidak diperlukan untuk menjalankan aplikasi dan aman dibuat ulang. File `.env` bukan file aplikasi untuk dibagikan, tetapi diperlukan untuk konfigurasi lokal; jangan menghapusnya jika masih digunakan dan jangan pernah mengirim kata sandinya.

### 5. Alur Kerja Aplikasi

1. Pengguna memilih satu PDF atau `.docx` dari dashboard.
2. `extract_document()` menentukan format berdasarkan ekstensi.
3. PDF diproses dengan `pypdf`; Word diproses dengan `python-docx`.
4. File dengan teks kurang dari 50 karakter ditolak. PDF scan tanpa lapisan teks tidak diproses karena aplikasi belum memiliki OCR.
5. `analyze_text()` menghitung empat skor indikator dan jumlah kata.
6. `save_analysis()` menyimpan skor dan rincian numerik ke PostgreSQL.
7. Dashboard menunjukkan hasil saat ini dan tab Riwayat membaca pemeriksaan terakhir.

File yang diunggah, nama file, teks hasil ekstraksi, dan metadata dokumen tidak disimpan ke tabel. Teks masih berada sementara di memori proses selama pemeriksaan berlangsung.

### 6. Rincian Metode Deteksi

#### 6.1 Karakter khusus — maksimum 25 poin

Menghitung em-dash (`—`), en-dash (`–`), zero-width space (`U+200B`), dan zero-width non-joiner (`U+200C`). Setiap kemunculan bernilai 5 poin, dengan batas 25.

#### 6.2 Frasa transisi — maksimum 30 poin

Mencari frasa Indonesia dan Inggris yang ditetapkan di `TRANSITION_PHRASES`, misalnya “selain itu”, “oleh karena itu”, “penting untuk dicatat”, “moreover”, dan “in conclusion”. Pencarian tidak membedakan kapitalisasi. Setiap kemunculan bernilai 5 poin, dengan batas 30.

#### 6.3 Keseragaman panjang kalimat — maksimum 30 poin

Kalimat dipecah dengan tanda titik, tanda tanya, dan tanda seru. Jumlah kata per kalimat dihitung, kemudian standar deviasi sampel ditentukan dengan `statistics.stdev`:

| Standar deviasi kata per kalimat | Poin |
|---|---:|
| Kurang dari 4,5 | 30 |
| 4,5 sampai kurang dari 6,5 | 18 |
| 6,5 atau lebih | 5 |

Minimal dua kalimat diperlukan. Jika kurang dari dua, indikator diberi 0 dan keterbatasannya ditampilkan.

#### 6.4 Struktur daftar berpoin — maksimum 15 poin

Regex pada `LIST_PATTERN` mencari baris daftar dengan judul yang diakhiri titik dua dan diikuti penjelasan, misalnya `1. Judul Poin: Penjelasan`. Setiap kecocokan bernilai 5 poin, dengan batas 15.

Jumlah skor seluruh indikator dibatasi maksimum 100. Statusnya adalah indikasi tinggi mulai 65, perlu ditinjau mulai 35, dan indikasi rendah di bawah 35. Ini bukan probabilitas terkalibrasi.

### 7. Peta Kode dan Penjelasan Fungsi

#### 7.1 `app.py` — tampilan dan alur pengguna

| Fungsi | Tugas |
|---|---|
| `apply_styles()` | Mengatur tema, warna, panel, dan tampilan responsif dashboard. |
| `render_sidebar()` | Menampilkan identitas aplikasi serta peringatan demo lokal tanpa login. |
| `show_findings()` | Menampilkan temuan empat indikator dan metadata dalam panel yang bisa dibuka. |
| `show_empty_state()` | Menjelaskan langkah unggah sebelum ada dokumen. |
| `analyze_upload()` | Memanggil ekstraksi dan analisis, menyimpan ringkasan, lalu menyimpan tampilan hasil di session state. |
| `show_analysis()` | Menampilkan status warna, skor, jumlah halaman/kata, dan rincian temuan. |
| `show_history()` | Membaca ringkasan terbaru dari PostgreSQL dan menampilkannya dalam tabel. |
| `show_database()` | Menampilkan nama database, versi server, status pgvector, dan isi tabel pemeriksaan. |
| `main()` | Menyatukan pemeriksaan koneksi serta tab analisis, riwayat, dan database. |

Contoh penanda kode yang digunakan di source:

```python
# Business-facing labels shown for the three rule-based score bands.
STATUS_TEXT = {...}

def analyze_upload(uploaded_file):
    """Extract and score one upload, then save only its summary to PostgreSQL."""
    ...
```

Komentar dan docstring menandai tujuan bagian/fungsi tanpa mengulang setiap baris kode. CSS berada di `apply_styles()` agar penataan visual tidak bercampur dengan ekstraksi dokumen.

#### 7.2 `detector.py` — ekstraksi dan mesin analisis

| Fungsi/konstanta | Tugas |
|---|---|
| `TRANSITION_PHRASES` | Daftar frasa yang diperiksa. |
| `SPECIAL_CHARACTERS` | Daftar karakter khusus beserta label tampilannya. |
| `LIST_PATTERN` | Regex pola daftar dengan judul dan titik dua. |
| `_extract_pdf()` | Membaca seluruh halaman, jumlah halaman, dan Creator/Producer PDF; menolak teks terlalu pendek. |
| `_extract_docx()` | Membaca paragraf, tabel, header/footer, dan nama pembuat DOCX. |
| `extract_document()` | Memilih fungsi ekstraksi berdasarkan jenis file. |
| `analyze_text()` | Menghitung skor dan temuan; tidak memanggil model atau membuat embedding. |

Penanda pada mesin analisis:

```python
def analyze_text(text):
    """Score four independent textual signals; no embedding/model is used here."""
    ...
```

#### 7.3 `database.py` — penyimpanan

| Elemen | Tugas |
|---|---|
| `AnalysisRecord` | Skema satu pemeriksaan: ID, jenis dokumen, skor, halaman, jumlah kata, JSON indikator, dan waktu. |
| `build_engine()` | Membuat koneksi dengan connection pool untuk PostgreSQL; menyediakan SQLite hanya untuk unit test. |
| `get_engine()` | Membaca `DATABASE_URL`, memvalidasi PostgreSQL, dan menggunakan kembali engine. |
| `check_database()` | Menguji koneksi sebelum dashboard ditampilkan. |
| `get_database_overview()` | Membaca nama database, versi PostgreSQL, dan status ekstensi pgvector. |
| `list_database_records()` | Membaca jumlah baris dan sampai 100 record terbaru beserta ID lengkap. |
| `save_analysis()` | Menyimpan ringkasan serta jumlah pola daftar, bukan teks yang cocok. |
| `list_recent_analyses()` | Membaca total, rata-rata skor, dan paling banyak 50 hasil terakhir. |

Tabel memiliki constraint tipe file, rentang skor, dan jumlah kata agar nilai yang tidak valid tidak diterima.

#### Melihat isi database dari aplikasi web

Setelah aplikasi berjalan, buka tab **Database** di halaman web. Tab ini membaca database PostgreSQL aktif dan menunjukkan nama database, versi server, status pgvector, jumlah baris `analysis_records`, serta tabel record terbaru. Pilih ID untuk melihat rincian kolom tersimpan. Jika belum pernah menjalankan analisis, tabel akan kosong; analisis dokumen terlebih dahulu untuk menambahkan baris. Tab **Riwayat** tetap tersedia sebagai ringkasan sederhana.

#### 7.4 Migrasi dan pgvector

`20261112_0001_create_analysis_records.py` membuat tabel riwayat. Migrasi berikutnya `20261112_0002_enable_pgvector.py` menjalankan:

```sql
CREATE EXTENSION IF NOT EXISTS vector;
```

Migrasi kedua hanya mengaktifkan ekstensi pgvector. Belum ada tipe kolom `VECTOR`, embedding model, pemrosesan teks ke embedding, atau query jarak/kemiripan. Hal ini mempertahankan spesifikasi rule-based semula dan menghindari pengiriman teks mahasiswa ke layanan/model embedding. Extension tidak dihapus saat downgrade karena dapat dipakai objek database lain.

`migrations/env.py` menghubungkan Alembic dengan URL database runtime. `alembic.ini` menunjuk lokasi folder migrasi dan file template `.mako` digunakan Alembic untuk membuat revisi baru.

### 8. Database, Privasi, dan Operasional

PostgreSQL menggunakan volume Docker `postgres_data`. Data riwayat tetap ada setelah kontainer dihentikan. Ringkasan yang disimpan meliputi ID, waktu, jenis dokumen, skor, jumlah halaman/kata, serta rincian angka indikator. Dokumen, nama file, teks, dan metadata sumber tidak disimpan.

- `docker compose down` menghentikan layanan tetapi mempertahankan volume.
- `docker compose down -v` menghapus volume dan seluruh riwayat demo secara permanen.
- Port aplikasi dibatasi ke `127.0.0.1:8501`, hanya untuk komputer lokal.
- Docker menggunakan `pgvector/pgvector:pg16`; startup menjalankan migrasi sebelum Streamlit.

### 9. Cara Menjalankan

1. Jalankan Docker Desktop dan pastikan `docker info` berhasil.
2. Salin `.env.example` menjadi `.env`, lalu tetapkan kata sandi database lokal.
3. Dari PowerShell di folder proyek, jalankan:

   ```powershell
   docker compose up --build
   ```

4. Buka `http://localhost:8501` di browser.
5. Lihat langkah rinci, pemecahan masalah, dan data di `README.md`.

### 10. Pengujian

Pengujian otomatis berada di `tests/` dan dijalankan dengan:

```powershell
python -m unittest discover -s tests -v
```

Pengujian mencakup skor indikator, ekstraksi paragraf/tabel DOCX, validasi PDF pendek, penolakan format DOC lama, penyimpanan riwayat, dan pemeriksaan bahwa isi daftar tidak disimpan sebagai teks.

### 11. Batasan dan Pengembangan Selanjutnya

- PDF scan tanpa teks digital belum dapat diproses; belum ada OCR.
- Dokumen Word `.doc` lama harus dikonversi ke `.docx`.
- DOCX tidak memiliki jumlah halaman tetap yang dapat dibaca konsisten oleh pustaka ini.
- Deteksi hanya rule-based dan dapat memberi false positive/negative.
- pgvector sudah aktif, tetapi belum dipakai untuk embeddings atau pencarian semantik.
- Aplikasi demo belum memiliki login, peran dosen/admin, pemisahan data institusi, HTTPS, audit pengguna, backup terjadwal, dan kebijakan retensi.

Sebelum digunakan oleh banyak dosen atau dijual ke perusahaan, tambahkan autentikasi dan otorisasi, pemisahan akses pengguna/institusi, backup dan restore, kebijakan penghapusan, HTTPS, uji beban, serta uji keamanan. Pengaktifan pgvector saja tidak membuat aplikasi menjadi produksi atau otomatis meningkatkan akurasi deteksi.

### 12. Kesimpulan

Proyek memisahkan antarmuka (`app.py`), ekstraksi dan aturan (`detector.py`), serta persistensi (`database.py`). PostgreSQL menyimpan ringkasan secara terstruktur dan ekstensi pgvector sudah aktif sesuai kebutuhan tugas. Tidak ada embedding/vector yang dihitung dalam versi ini; skor tetap berasal dari empat aturan yang dapat diperiksa. Struktur tersebut menjadi fondasi yang jelas untuk pengembangan berikutnya, tetapi belum boleh dipasarkan sebagai layanan produksi sebelum kontrol keamanan dan operasional dilengkapi.
