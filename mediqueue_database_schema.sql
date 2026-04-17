-- ============================================================
-- MEDIQUEUE - Smart Hospital & Queue Management System
-- Database: MySQL 8.0+
-- ============================================================

CREATE DATABASE IF NOT EXISTS mediqueue DEFAULT CHARACTER SET utf8mb4;
USE mediqueue;

-- ==========================================
-- TABLE: departments
-- ==========================================
CREATE TABLE IF NOT EXISTS departments (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL UNIQUE,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ==========================================
-- TABLE: users
-- ==========================================
CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(150) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(20) NOT NULL,
    phone VARCHAR(20),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ==========================================
-- TABLE: doctors
-- ==========================================
CREATE TABLE IF NOT EXISTS doctors (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    department_id INT,
    specialization VARCHAR(100),
    qualification VARCHAR(200),
    experience_years INT DEFAULT 0,
    available BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (department_id) REFERENCES departments(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ==========================================
-- TABLE: patients
-- ==========================================
CREATE TABLE IF NOT EXISTS patients (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    date_of_birth DATE,
    gender VARCHAR(10),
    address TEXT,
    blood_group VARCHAR(5),
    medical_history TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ==========================================
-- TABLE: appointments
-- ==========================================
CREATE TABLE IF NOT EXISTS appointments (
    id INT AUTO_INCREMENT PRIMARY KEY,
    patient_id INT NOT NULL,
    doctor_id INT NOT NULL,
    appointment_date DATE NOT NULL,
    appointment_time TIME NOT NULL,
    status VARCHAR(20) DEFAULT 'pending',
    reason TEXT,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (patient_id) REFERENCES patients(id) ON DELETE CASCADE,
    FOREIGN KEY (doctor_id) REFERENCES doctors(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ==========================================
-- TABLE: queue
-- ==========================================
CREATE TABLE IF NOT EXISTS queue (
    id INT AUTO_INCREMENT PRIMARY KEY,
    appointment_id INT NOT NULL,
    doctor_id INT NOT NULL,
    patient_id INT NOT NULL,
    queue_number INT NOT NULL,
    status VARCHAR(20) DEFAULT 'waiting',
    check_in_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    start_time TIMESTAMP NULL DEFAULT NULL,
    end_time TIMESTAMP NULL DEFAULT NULL,
    queue_date DATE,
    FOREIGN KEY (appointment_id) REFERENCES appointments(id) ON DELETE CASCADE,
    FOREIGN KEY (doctor_id) REFERENCES doctors(id) ON DELETE CASCADE,
    FOREIGN KEY (patient_id) REFERENCES patients(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ==========================================
-- SEED: departments
-- ==========================================
INSERT IGNORE INTO departments (name, description) VALUES
('Cardiology',       'Heart and cardiovascular system care'),
('Neurology',        'Brain and nervous system disorders'),
('Orthopedics',      'Bone, joint and muscle care'),
('General Practice', 'General health and routine checkups'),
('Radiology',        'Medical imaging and diagnostics'),
('Pediatrics',       'Children healthcare'),
('Dermatology',      'Skin, hair and nail disorders');

-- ==========================================
-- DEFAULT ADMIN ACCOUNT
-- ==========================================
-- Run this to create the admin:
--   python seed_admin.py
--
-- Credentials:
--   Email:    admin@mediqueue.com
--   Password: admin123
-- ==========================================
