-- Membuat database jika belum ada
CREATE DATABASE IF NOT EXISTS ecommerce;
USE ecommerce;

-- Tabel pengguna (users)
CREATE TABLE users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) NOT NULL UNIQUE,
    email VARCHAR(100) NOT NULL UNIQUE,
    phone_number VARCHAR(15) NOT NULL,
    address TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_username (username)
);

-- Tabel produk (products)
CREATE TABLE products (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    price DECIMAL(10, 2) NOT NULL CHECK (price >= 0),
    stock INT NOT NULL CHECK (stock >= 0),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_name (name)
);

-- Tabel pesanan (orders)
CREATE TABLE orders (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    product_id INT NOT NULL,
    quantity INT NOT NULL CHECK (quantity > 0),
    total_price DECIMAL(10, 2) NOT NULL CHECK (total_price >= 0),
    status ENUM('pending', 'completed', 'cancelled') DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE
);

-- Tabel ulasan (reviews)
CREATE TABLE reviews (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    product_id INT NOT NULL,
    rating INT NOT NULL CHECK (rating >= 1 AND rating <= 5),
    comment TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE
);

-- Data sample users (dikurangi dan kapitalisasi nama)
INSERT INTO users (username, email, phone_number, address) VALUES
('Agus Saputra', 'agus.saputra@gmail.com', '081234567890', 'Jl. Merdeka No. 10, Jakarta'),
('Siti Nurhaliza', 'siti.nurhaliza@yahoo.com', '085678912345', 'Jl. Sudirman No. 25, Bandung'),
('Budi Rahman', 'budi.rahman@outlook.com', '087890123456', 'Jl. Gatot Subroto No. 15, Surabaya');

-- Data sample products (dikurangi)
INSERT INTO products (name, description, price, stock) VALUES
('Laptop ASUS ROG', 'Laptop gaming dengan prosesor Intel i7 dan GPU RTX 3060', 25000000.00, 15),
('Smartphone Xiaomi 13', 'Smartphone 5G dengan kamera 108MP', 8000000.00, 30),
('Baju Batik Pria', 'Baju batik modern dengan motif parang', 250000.00, 50);

-- Data sample orders (dikurangi)
INSERT INTO orders (user_id, product_id, quantity, total_price, status) VALUES
(1, 1, 1, 25000000.00, 'completed'),
(2, 2, 2, 16000000.00, 'completed'),
(3, 3, 3, 750000.00, 'pending');

-- Data sample reviews (dikurangi)
INSERT INTO reviews (user_id, product_id, rating, comment) VALUES
(1, 1, 5, 'Laptopnya kencang banget, cocok buat gaming!'),
(2, 2, 4, 'Kamera oke, tapi baterai agak cepat habis.'),
(3, 3, 5, 'Batiknya elegan, nyaman dipakai.');
