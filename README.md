# Sistem Integrasi Layanan E-Commerce

## KELOMPOK 3 - SI4605
1. Ahmad Fauzi (1202220263)
2. Deridda Ahmad Zarrar Ray (1202223353)
3. I Putu Bagus Widya Wijaya Pratama (1202223040)
4. Muhammad Rafi Syihan (1202223384)
5. Vilson (1202220199)

Proyek ini dikembangkan untuk **Ujian Tengah Semester (UTS) mata kuliah Enterprise Application Integration (EAI)** Kelompok 3. Sistem ini mengimplementasikan komunikasi antar layanan untuk platform e-commerce tanpa menggunakan API Gateway, dengan memanfaatkan REST API dalam format data JSON. Sistem terdiri dari empat layanan independen: **Layanan Pengguna**, **Layanan Produk**, **Layanan Pesanan**, dan **Layanan Ulasan**, yang masing-masing berperan sebagai **penyedia** dan **konsumen** data.

## Daftar Isi
1. [Overview Proyek](#Overview-proyek)
2. [Arsitektur Sistem](#arsitektur-sistem)
3. [Layanan dan Dokumentasi API](#layanan-dan-dokumentasi-api)
   - [Layanan Pengguna](#layanan-pengguna)
   - [Layanan Produk](#layanan-produk)
   - [Layanan Pesanan](#layanan-pesanan)
   - [Layanan Ulasan](#layanan-ulasan)
4. [Komunikasi Antar Layanan](#komunikasi-antar-layanan)
   - [Peran Provider–Consumer](#peran-providerconsumer)
5. [Petunjuk Pengaturan](#petunjuk-pengaturan)
6. [Skema Database](#skema-database)
7. [Data Sampel](#data-sampel)
8. [Teknologi yang Digunakan](#teknologi-yang-digunakan)
9. [Catatan](#catatan)

---

## Overview Proyek
Sistem ini dirancang untuk mensimulasikan platform e-commerce di mana:
- **Pengguna** dapat dikelola (dibuat, diperbarui, dihapus) dan riwayat pesanan mereka dapat dilihat.
- **Produk** dapat dikelola, dan ulasan produk dapat diakses.
- **Pesanan** dapat dibuat, diperbarui, atau dihapus, dengan integrasi data pengguna dan produk.
- **Ulasan** dapat dikelola untuk produk, menghubungkan pengguna dan produk.

Setiap layanan berkomunikasi langsung dengan layanan lain melalui permintaan HTTP (REST API) menggunakan JSON. Sistem ini menggunakan database MySQL untuk menyimpan data dan Flask (Python) untuk backend, dengan antarmuka web untuk interaksi.

## Arsitektur Sistem
Sistem terdiri dari empat microservices yang berjalan pada port berbeda:
- **Layanan Pengguna**: Port 5001
- **Layanan Produk**: Port 5002
- **Layanan Pesanan**: Port 5003
- **Layanan Ulasan**: Port 5004

Setiap layanan memiliki tabel database sendiri dalam database `ecommerce` dan berkomunikasi langsung dengan layanan lain untuk mengambil atau memvalidasi data. Arsitektur ini tidak menggunakan API Gateway, melainkan mengandalkan panggilan HTTP antar layanan.

## Layanan dan Dokumentasi API

### Layanan Pengguna
**Port**: 5001  
**Peran**: 
- **Penyedia**: Menyediakan data pengguna (daftar, detail, buat, perbarui, hapus).
- **Konsumen**: Mengambil riwayat pesanan dari Layanan Pesanan.

#### Endpoint
1. **GET /health**
   - **Deskripsi**: Memeriksa kesehatan layanan dengan memverifikasi koneksi database.
   - **Respons**:
     ```json
     { "status": "healthy" }
     ```
     - Status: 200 OK
     - Error: 503 Service Unavailable (`{ "status": "unhealthy", "error": "Database tidak tersedia" }`)

2. **GET /api/users**
   - **Deskripsi**: Mengambil semua pengguna.
   - **Respons**:
     ```json
     [
       {
         "id": 1,
         "username": "Agus Saputra",
         "email": "agus.saputra@gmail.com",
         "phone_number": "081234567890",
         "address": "Jl. Merdeka No. 10, Jakarta"
       }
     ]
     ```
     - Status: 200 OK

3. **GET /api/users/<user_id>**
   - **Deskripsi**: Mengambil pengguna berdasarkan ID.
   - **Respons**:
     ```json
     {
       "id": 1,
       "username": "Agus Saputra",
       "email": "agus.saputra@gmail.com",
       "phone_number": "081234567890",
       "address": "Jl. Merdeka No. 10, Jakarta"
     }
     ```
     - Status: 200 OK
     - Error: 404 Not Found (`{ "error": "Pengguna tidak ditemukan" }`)

4. **POST /api/users**
   - **Deskripsi**: Membuat pengguna baru.
   - **Body Permintaan**:
     ```json
     {
       "username": "John Doe",
       "email": "john.doe@example.com",
       "phone_number": "081234567890",
       "address": "Jl. Contoh No. 123"
     }
     ```
   - **Respons**:
     ```json
     {
       "id": 4,
       "username": "John Doe",
       "email": "john.doe@example.com",
       "phone_number": "081234567890",
       "address": "Jl. Contoh No. 123"
     }
     ```
     - Status: 201 Created
     - Error: 400 Bad Request (`{ "error": "Username, email, nomor telepon, dan alamat wajib diisi" }`)

5. **PUT /api/users/<user_id>**
   - **Deskripsi**: Memperbarui pengguna yang ada.
   - **Body Permintaan**: Sama seperti POST.
   - **Respons**: Sama seperti POST.
   - **Status**: 200 OK
   - **Error**: 400 Bad Request, 404 Not Found

6. **DELETE /api/users/<user_id>**
   - **Deskripsi**: Menghapus pengguna, dengan pemeriksaan pesanan atau ulasan yang ada.
   - **Respons**:
     ```json
     { "message": "Pengguna berhasil dihapus" }
     ```
     - Status: 200 OK
     - Error: 400 Bad Request (`{ "error": "Tidak dapat menghapus pengguna dengan pesanan yang ada" }`), 404 Not Found, 503 Service Unavailable

7. **GET /api/users/<user_id>/orders**
   - **Deskripsi**: Mengambil riwayat pesanan pengguna dari Layanan Pesanan.
   - **Respons**:
     ```json
     [
       {
         "id": 1,
         "user_id": 1,
         "product_id": 1,
         "quantity": 1,
         "total_price": 25000000.00,
         "status": "completed",
         "created_at": "2025-04-25T10:00:00"
       }
     ]
     ```
     - Status: 200 OK
     - Error: 503 Service Unavailable (`{ "error": "Layanan pesanan tidak tersedia" }`)

### Layanan Produk
**Port**: 5002  
**Peran**: 
- **Penyedia**: Menyediakan data produk (daftar, detail, buat, perbarui, hapus).
- **Konsumen**: Mengambil ulasan produk dari Layanan Ulasan.

#### Endpoint
1. **GET /health**
   - Sama seperti Layanan Pengguna.

2. **GET /api/products**
   - **Deskripsi**: Mengambil semua produk.
   - **Respons**:
     ```json
     [
       {
         "id": 1,
         "name": "Laptop ASUS ROG",
         "description": "Laptop gaming dengan prosesor Intel i7 dan GPU RTX 3060",
         "price": 25000000.00,
         "stock": 15
       }
     ]
     ```
     - Status: 200 OK

3. **GET /api/products/<product_id>**
   - **Deskripsi**: Mengambil produk berdasarkan ID.
   - **Respons**:
     ```json
     {
       "id": 1,
       "name": "Laptop ASUS ROG",
       "description": "Laptop gaming dengan prosesor Intel i7 dan GPU RTX 3060",
       "price": 25000000.00,
       "stock": 15
     }
     ```
     - Status: 200 OK
     - Error: 404 Not Found (`{ "error": "Produk tidak ditemukan" }`)

4. **POST /api/products**
   - **Deskripsi**: Membuat produk baru.
   - **Body Permintaan**:
     ```json
     {
       "name": "Produk Baru",
       "description": "Deskripsi di sini",
       "price": 1000000.00,
       "stock": 10
     }
     ```
   - **Respons**: Sama seperti GET /api/products/<product_id>.
   - **Status**: 201 Created
   - **Error**: 400 Bad Request (`{ "error": "Nama, harga, dan stok wajib diisi" }`)

5. **PUT /api/products/<product_id>**
   - **Deskripsi**: Memperbarui produk yang ada.
   - **Body Permintaan**: Sama seperti POST.
   - **Respons**: Sama seperti POST.
   - **Status**: 200 OK
   - **Error**: 400 Bad Request, 404 Not Found

6. **DELETE /api/products/<product_id>**
   - **Deskripsi**: Menghapus produk, dengan pemeriksaan pesanan atau ulasan yang ada.
   - **Respons**:
     ```json
     { "message": "Produk berhasil dihapus" }
     ```
     - Status: 200 OK
     - Error: 400 Bad Request (`{ "error": "Tidak dapat menghapus produk dengan pesanan yang ada" }`), 404 Not Found, 503 Service Unavailable

7. **GET /api/products/<product_id>/reviews**
   - **Deskripsi**: Mengambil ulasan untuk produk dari Layanan Ulasan.
   - **Respons**:
     ```json
     [
       {
         "id": 1,
         "user_id": 1,
         "product_id": 1,
         "rating": 5,
         "comment": "Laptopnya kencang banget, cocok buat gaming!",
         "created_at": "2025-04-25T10:00:00"
       }
     ]
     ```
     - Status: 200 OK
     - Error: 503 Service Unavailable (`{ "error": "Layanan ulasan tidak tersedia" }`)

### Layanan Pesanan
**Port**: 5003  
**Peran**: 
- **Penyedia**: Menyediakan data pesanan (daftar, buat, perbarui, hapus).
- **Konsumen**: Memvalidasi data pengguna dan produk dari Layanan Pengguna dan Layanan Produk.

#### Endpoint
1. **GET /health**
   - Sama seperti Layanan Pengguna.

2. **GET /api/orders**
   - **Deskripsi**: Mengambil semua pesanan, dapat difilter berdasarkan user_id atau product_id.
   - **Parameter Kueri**:
     - `user_id`: Filter berdasarkan ID pengguna.
     - `product_id`: Filter berdasarkan ID produk.
   - **Respons**:
     ```json
     [
       {
         "id": 1,
         "user_id": 1,
         "product_id": 1,
         "quantity": 1,
         "total_price": 25000000.00,
         "status": "completed",
         "created_at": "2025-04-25T10:00:00"
       }
     ]
     ```
     - Status: 200 OK

3. **POST /api/orders**
   - **Deskripsi**: Membuat pesanan baru, memvalidasi pengguna dan produk.
   - **Body Permintaan**:
     ```json
     {
       "user_id": 1,
       "product_id": 1,
       "quantity": 1,
       "status": "pending"
     }
     ```
   - **Respons**:
     ```json
     {
       "id": 4,
       "user_id": 1,
       "product_id": 1,
       "quantity": 1,
       "total_price": 25000000.00,
       "status": "pending"
     }
     ```
     - Status: 201 Created
     - Error: 400 Bad Request (`{ "error": "ID pengguna tidak valid" }`, `{ "error": "Stok tidak cukup" }`), 503 Service Unavailable

4. **PUT /api/orders/<order_id>**
   - **Deskripsi**: Memperbarui pesanan yang ada, menyesuaikan stok.
   - **Body Permintaan**: Sama seperti POST.
   - **Respons**: Sama seperti POST.
   - **Status**: 200 OK
   - **Error**: 400 Bad Request, 404 Not Found, 503 Service Unavailable

5. **DELETE /api/orders/<order_id>**
   - **Deskripsi**: Menghapus pesanan, mengembalikan stok produk.
   - **Respons**:
     ```json
     { "message": "Pesanan berhasil dihapus" }
     ```
     - Status: 200 OK
     - Error: 404 Not Found

### Layanan Ulasan
**Port**: 5004  
**Peran**: 
- **Penyedia**: Menyediakan data ulasan (daftar, buat, perbarui, hapus).
- **Konsumen**: Memvalidasi data pengguna dan produk dari Layanan Pengguna dan Layanan Produk.

#### Endpoint
1. **GET /health**
   - Sama seperti Layanan Pengguna.

2. **GET /api/reviews**
   - **Deskripsi**: Mengambil semua ulasan, dapat difilter berdasarkan user_id atau product_id.
   - **Parameter Kueri**:
     - `user_id`: Filter berdasarkan ID pengguna.
     - `product_id`: Filter berdasarkan ID produk.
   - **Respons**:
     ```json
     [
       {
         "id": 1,
         "user_id": 1,
         "product_id": 1,
         "rating": 5,
         "comment": "Laptopnya kencang banget, cocok buat gaming!",
         "created_at": "2025-04-25T10:00:00"
       }
     ]
     ```
     - Status: 200 OK

3. **POST /api/reviews**
   - **Deskripsi**: Membuat ulasan baru, memvalidasi pengguna dan produk.
   - **Body Permintaan**:
     ```json
     {
       "user_id": 1,
       "product_id": 1,
       "rating": 5,
       "comment": "Produk hebat!"
     }
     ```
   - **Respons**:
     ```json
     {
       "id": 4,
       "user_id": 1,
       "product_id": 1,
       "rating": 5,
       "comment": "Produk hebat!"
     }
     ```
     - Status: 201 Created
     - Error: 400 Bad Request (`{ "error": "ID pengguna tidak valid" }`, `{ "error": "Rating harus bilangan bulat antara 1 dan 5" }`), 503 Service Unavailable

4. **PUT /api/reviews/<review_id>**
   - **Deskripsi**: Memperbarui ulasan yang ada.
   - **Body Permintaan**: Sama seperti POST.
   - **Respons**: Sama seperti POST.
   - **Status**: 200 OK
   - **Error**: 400 Bad Request, 404 Not Found, 503 Service Unavailable

5. **DELETE /api/reviews/<review_id>**
   - **Deskripsi**: Menghapus ulasan.
   - **Respons**:
     ```json
     { "message": "Ulasan berhasil dihapus" }
     ```
     - Status: 200 OK
     - Error: 404 Not Found

## Komunikasi Antar Layanan
Sistem ini mengimplementasikan komunikasi langsung antar layanan menggunakan REST API melalui HTTP. Berikut adalah interaksi utama:

### Peran Provider–Consumer
Berikut adalah ringkasan peran masing-masing layanan sebagai penyedia dan konsumen dalam sistem:

- **Layanan Pengguna**:
  - **Penyedia**: Menyediakan data pengguna (misalnya, detail pengguna) untuk Layanan Pesanan dan Layanan Ulasan melalui endpoint seperti `GET /api/users/<user_id>`.
  - **Konsumen**: Mengambil riwayat pesanan dari Layanan Pesanan melalui endpoint `GET /api/orders?user_id=<user_id>` untuk menampilkan pesanan pengguna.

- **Layanan Produk**:
  - **Penyedia**: Menyediakan data produk (misalnya, detail produk dan stok) untuk Layanan Pesanan dan Layanan Ulasan melalui endpoint seperti `GET /api/products/<product_id>`.
  - **Konsumen**: Mengambil ulasan produk dari Layanan Ulasan melalui endpoint `GET /api/reviews?product_id=<product_id>` untuk menampilkan ulasan produk.

- **Layanan Pesanan**:
  - **Penyedia**: Menyediakan data pesanan untuk Layanan Pengguna melalui endpoint `GET /api/orders?user_id=<user_id>`.
  - **Konsumen**: Memvalidasi data pengguna dari Layanan Pengguna (`GET /api/users/<user_id>`) dan data produk dari Layanan Produk (`GET /api/products/<product_id>`) saat membuat atau memperbarui pesanan.

- **Layanan Ulasan**:
  - **Penyedia**: Menyediakan data ulasan untuk Layanan Produk melalui endpoint `GET /api/reviews?product_id=<product_id>`.
  - **Konsumen**: Memvalidasi data pengguna dari Layanan Pengguna (`GET /api/users/<user_id>`) dan data produk dari Layanan Produk (`GET /api/products/<product_id>`) saat membuat atau memperbarui ulasan.

### Interaksi Utama
1. **Layanan Pesanan**:
   - **Konsumen**: 
     - Mengambil data pengguna dari Layanan Pengguna (`GET /api/users/<user_id>`) untuk memvalidasi keberadaan pengguna saat membuat/memperbarui pesanan.
     - Mengambil data produk dari Layanan Produk (`GET /api/products/<product_id>`) untuk memvalidasi keberadaan produk dan stok.
   - **Penyedia**: Menyediakan data pesanan untuk Layanan Pengguna (`GET /api/orders?user_id=<user_id>`).
   - **Contoh Alur**:
     - Untuk membuat pesanan, Layanan Pesanan:
       1. Memvalidasi pengguna dengan memanggil `http://localhost:5001/api/users/<user_id>`.
       2. Memvalidasi produk dan stok dengan memanggil `http://localhost:5002/api/products/<product_id>`.
       3. Memperbarui stok produk dan membuat pesanan di database.

2. **Layanan Produk**:
   - **Konsumen**: Mengambil ulasan dari Layanan Ulasan (`GET /api/reviews?product_id=<product_id>`).
   - **Penyedia**: Menyediakan data produk untuk Layanan Pesanan dan Layanan Ulasan.
   - **Contoh Alur**:
     - Untuk menampilkan ulasan produk, Layanan Produk memanggil `http://localhost:5004/api/reviews?product_id=<product_id>`.

3. **Layanan Ulasan**:
   - **Konsumen**: 
     - Memvalidasi pengguna dengan memanggil Layanan Pengguna (`GET /api/users/<user_id>`).
     - Memvalidasi produk dengan memanggil Layanan Produk (`GET /api/products/<product_id>`).
   - **Penyedia**: Menyediakan data ulasan untuk Layanan Produk.
   - **Contoh Alur**:
     - Untuk membuat ulasan, Layanan Ulasan memvalidasi pengguna dan produk sebelum menyimpan.

4. **Layanan Pengguna**:
   - **Konsumen**: Mengambil riwayat pesanan dari Layanan Pesanan (`GET /api/orders?user_id=<user_id>`).
   - **Penyedia**: Menyediakan data pengguna untuk Layanan Pesanan dan Layanan Ulasan.
   - **Contoh Alur**:
     - Untuk menampilkan pesanan pengguna, Layanan Pengguna memanggil `http://localhost:5003/api/orders?user_id=<user_id>`.

### Penanganan Error
- Layanan mengembalikan kode status HTTP yang sesuai (misalnya, 400 untuk input tidak valid, 404 untuk tidak ditemukan, 503 untuk layanan tidak tersedia).
- Pencatatan (logging) diimplementasikan untuk melacak permintaan, error, dan interaksi layanan.

## Petunjuk Pengaturan
1. **Prasyarat**:
   - Python 3.8+
   - MySQL Server
   - pip (manajer paket Python) flask, mysql-connector-python, requests

2. **Instal Dependensi**:
   ```bash
   pip install flask flask-cors mysql-connector-python requests
   ```

3. **Pengaturan Database**:
   - Buat database `ecommerce` dan tabel menggunakan `ecommerce.sql`:
     ```bash
     mysql -u root -p < ecommerce.sql
     ```
   - Pastikan MySQL berjalan dan kredensial sesuai dengan file `.env`.

4. **Konfigurasi Lingkungan**:
   - Perbarui file `.env` dengan kredensial MySQL dan URL layanan jika diperlukan.

5. **Jalankan Layanan**:
   - Jalankan setiap layanan di jendela terminal terpisah:
     ```bash
     python user_service/user_service.py
     python product_service/product_service.py
     python order_service/order_service.py
     python review_service/review_service.py
     ```
   - Layanan akan berjalan pada port 5001, 5002, 5003, dan 5004.

6. **Akses Sistem**:
   - Buka browser dan kunjungi:
     - Layanan Pengguna: `http://localhost:5001`
     - Layanan Produk: `http://localhost:5002`
     - Layanan Pesanan: `http://localhost:5003`
     - Layanan Ulasan: `http://localhost:5004`
   - Gunakan antarmuka web untuk mengelola pengguna, produk, pesanan, dan ulasan.

## Skema Database
Database `ecommerce` mencakup empat tabel:
- **users**: Menyimpan informasi pengguna (id, username, email, phone_number, address).
- **products**: Menyimpan detail produk (id, name, description, price, stock).
- **orders**: Menyimpan data pesanan (id, user_id, product_id, quantity, total_price, status).
- **reviews**: Menyimpan data ulasan (id, user_id, product_id, rating, comment).

Lihat `ecommerce.sql` untuk skema lengkap dan data sampel.

## Data Sampel
Database telah diisi dengan data awal:
- 3 pengguna (misalnya, Agus Saputra, Siti Nurhaliza).
- 3 produk (misalnya, Laptop ASUS ROG, Smartphone Xiaomi 13).
- 3 pesanan (misalnya, pengguna 1 memesan 1 laptop).
- 3 ulasan (misalnya, ulasan 5 bintang untuk laptop).

## Teknologi yang Digunakan
- **Backend**: Python, Flask, Flask-CORS
- **Database**: MySQL
- **Frontend**: HTML, Tailwind CSS, JavaScript
- **Komunikasi**: REST API (HTTP, JSON)
- **Pencatatan**: Modul `logging` Python
- **Lingkungan**: File `.env` untuk konfigurasi

## Catatan
- Sistem menggunakan komunikasi langsung antar layanan, yang dapat menyebabkan latensi atau masalah ketergantungan jika salah satu layanan mati. Peningkatan di masa depan dapat mencakup API Gateway atau circuit breaker.
- Antarmuka web menyediakan cara yang ramah pengguna untuk berinteraksi dengan layanan, dengan modal untuk menambah/mengedit data dan tabel dinamis untuk melihat data.
- Data sampel dibuat minimal untuk menjaga sistem tetap ringan namun cukup untuk menunjukkan fungsionalitas.
- Proyek ini mematuhi praktik terbaik REST API, dengan metode HTTP dan kode status yang sesuai.
- Penanganan error memastikan ketahanan sistem, dengan validasi untuk input dan ketergantungan.