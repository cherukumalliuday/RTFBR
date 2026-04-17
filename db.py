import os
import psycopg2
import psycopg2.extras
from datetime import timedelta

def get_connection():
    return psycopg2.connect(
        os.environ["DATABASE_URL"],
        cursor_factory=psycopg2.extras.RealDictCursor
    )

def serialize_row(row):
    result = {}
    for key, val in dict(row).items():
        if hasattr(val, "isoformat"):
            result[key] = val.isoformat()
        elif isinstance(val, timedelta):
            total = int(val.total_seconds())
            h, rem = divmod(total, 3600)
            m, s = divmod(rem, 60)
            result[key] = f"{h:02d}:{m:02d}:{s:02d}"
        else:
            result[key] = val
    return result

def init_db():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS departments (
            id SERIAL PRIMARY KEY,
            name VARCHAR(100) NOT NULL UNIQUE,
            description TEXT,
            created_at TIMESTAMP DEFAULT NOW()
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            name VARCHAR(100) NOT NULL,
            email VARCHAR(150) NOT NULL UNIQUE,
            password_hash VARCHAR(255) NOT NULL,
            role VARCHAR(20) NOT NULL,
            phone VARCHAR(20),
            created_at TIMESTAMP DEFAULT NOW()
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS doctors (
            id SERIAL PRIMARY KEY,
            user_id INT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            department_id INT REFERENCES departments(id),
            specialization VARCHAR(100),
            qualification VARCHAR(200),
            experience_years INT DEFAULT 0,
            available BOOLEAN DEFAULT TRUE,
            created_at TIMESTAMP DEFAULT NOW()
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS patients (
            id SERIAL PRIMARY KEY,
            user_id INT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            date_of_birth DATE,
            gender VARCHAR(10),
            address TEXT,
            blood_group VARCHAR(5),
            medical_history TEXT,
            created_at TIMESTAMP DEFAULT NOW()
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS appointments (
            id SERIAL PRIMARY KEY,
            patient_id INT NOT NULL REFERENCES patients(id) ON DELETE CASCADE,
            doctor_id INT NOT NULL REFERENCES doctors(id) ON DELETE CASCADE,
            appointment_date DATE NOT NULL,
            appointment_time TIME NOT NULL,
            status VARCHAR(20) DEFAULT 'pending',
            reason TEXT,
            notes TEXT,
            created_at TIMESTAMP DEFAULT NOW()
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS queue (
            id SERIAL PRIMARY KEY,
            appointment_id INT NOT NULL REFERENCES appointments(id) ON DELETE CASCADE,
            doctor_id INT NOT NULL REFERENCES doctors(id) ON DELETE CASCADE,
            patient_id INT NOT NULL REFERENCES patients(id) ON DELETE CASCADE,
            queue_number INT NOT NULL,
            status VARCHAR(20) DEFAULT 'waiting',
            check_in_time TIMESTAMP DEFAULT NOW(),
            start_time TIMESTAMP,
            end_time TIMESTAMP,
            queue_date DATE DEFAULT CURRENT_DATE
        )
    """)

    conn.commit()
    cur.close()
    conn.close()
