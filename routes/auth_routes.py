from flask import Blueprint, request, jsonify, session
from werkzeug.security import generate_password_hash, check_password_hash
from db import get_connection, serialize_row

auth_bp = Blueprint("auth", __name__)

@auth_bp.route("/api/register", methods=["POST"])
def register():
    data = request.get_json()
    name = data.get("name")
    email = data.get("email")
    password = data.get("password")
    role = data.get("role", "patient")
    phone = data.get("phone")

    if not all([name, email, password]):
        return jsonify({"error": "Name, email and password are required"}), 400

    if role not in ("patient", "doctor", "admin"):
        return jsonify({"error": "Invalid role"}), 400

    password_hash = generate_password_hash(password)

    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO users (name, email, password_hash, role, phone) VALUES (%s, %s, %s, %s, %s) RETURNING id",
            (name, email, password_hash, role, phone)
        )
        user_id = cur.fetchone()["id"]

        if role == "patient":
            dob = data.get("date_of_birth")
            gender = data.get("gender")
            address = data.get("address")
            blood_group = data.get("blood_group")
            cur.execute(
                "INSERT INTO patients (user_id, date_of_birth, gender, address, blood_group) VALUES (%s, %s, %s, %s, %s)",
                (user_id, dob, gender, address, blood_group)
            )
        elif role == "doctor":
            department_id = data.get("department_id")
            specialization = data.get("specialization")
            qualification = data.get("qualification")
            experience_years = data.get("experience_years", 0)
            cur.execute(
                "INSERT INTO doctors (user_id, department_id, specialization, qualification, experience_years) VALUES (%s, %s, %s, %s, %s)",
                (user_id, department_id, specialization, qualification, experience_years)
            )

        conn.commit()
        cur.close()
        conn.close()
        return jsonify({"message": "Registration successful", "user_id": user_id}), 201

    except Exception as e:
        if "duplicate" in str(e).lower() or "1062" in str(e):
            return jsonify({"error": "Email already registered"}), 409
        return jsonify({"error": str(e)}), 500

@auth_bp.route("/api/login", methods=["POST"])
def login():
    data = request.get_json()
    email = data.get("email")
    password = data.get("password")

    if not all([email, password]):
        return jsonify({"error": "Email and password are required"}), 400

    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM users WHERE email = %s", (email,))
    user = cur.fetchone()
    cur.close()
    conn.close()

    if not user or not check_password_hash(user["password_hash"], password):
        return jsonify({"error": "Invalid email or password"}), 401

    session["user_id"] = user["id"]
    session["role"] = user["role"]
    session["name"] = user["name"]

    return jsonify({
        "message": "Login successful",
        "user": {
            "id": user["id"],
            "name": user["name"],
            "email": user["email"],
            "role": user["role"]
        }
    })

@auth_bp.route("/api/logout", methods=["POST"])
def logout():
    session.clear()
    return jsonify({"message": "Logged out successfully"})

@auth_bp.route("/api/me", methods=["GET"])
def get_current_user():
    if "user_id" not in session:
        return jsonify({"error": "Not logged in"}), 401

    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT id, name, email, role, phone, created_at FROM users WHERE id = %s", (session["user_id"],))
    user = cur.fetchone()
    cur.close()
    conn.close()

    if not user:
        session.clear()
        return jsonify({"error": "User not found"}), 404

    user = serialize_row(user)
    return jsonify({"user": user})
