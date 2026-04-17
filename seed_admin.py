import os
import sys
sys.path.insert(0, os.path.dirname(__file__))

from werkzeug.security import generate_password_hash
from db import get_connection, init_db

def seed():
    init_db()
    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        "INSERT INTO users (name, email, password_hash, role) VALUES (%s, %s, %s, %s) ON CONFLICT (email) DO NOTHING RETURNING id",
        ("Admin Root", "admin@mediqueue.com", generate_password_hash("admin123"), "admin")
    )
    result = cur.fetchone()
    if result:
        print("Admin created: admin@mediqueue.com / admin123")
    else:
        print("Admin already exists.")

    conn.commit()
    cur.close()
    conn.close()

if __name__ == "__main__":
    seed()
