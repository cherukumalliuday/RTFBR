from flask import Blueprint, request, jsonify, session
from auth import login_required, role_required
from db import get_connection, serialize_row

patient_bp = Blueprint("patient", __name__)

@patient_bp.route("/api/patients/profile", methods=["GET"])
@role_required("patient")
def get_patient_profile():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT p.*, u.name, u.email, u.phone
        FROM patients p
        JOIN users u ON p.user_id = u.id
        WHERE p.user_id = %s
    """, (session["user_id"],))
    patient = cur.fetchone()
    cur.close()
    conn.close()

    if not patient:
        return jsonify({"error": "Patient profile not found"}), 404

    return jsonify({"patient": serialize_row(patient)})

@patient_bp.route("/api/patients/profile", methods=["PUT"])
@role_required("patient")
def update_patient_profile():
    data = request.get_json()
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        UPDATE patients SET date_of_birth = %s, gender = %s, address = %s,
        blood_group = %s, medical_history = %s
        WHERE user_id = %s
    """, (
        data.get("date_of_birth"), data.get("gender"), data.get("address"),
        data.get("blood_group"), data.get("medical_history"), session["user_id"]
    ))

    if data.get("name") or data.get("phone"):
        updates = []
        values = []
        if data.get("name"):
            updates.append("name = %s")
            values.append(data["name"])
        if data.get("phone"):
            updates.append("phone = %s")
            values.append(data["phone"])
        values.append(session["user_id"])
        cur.execute(f"UPDATE users SET {', '.join(updates)} WHERE id = %s", values)

    conn.commit()
    cur.close()
    conn.close()
    return jsonify({"message": "Profile updated successfully"})

@patient_bp.route("/api/patients/appointments", methods=["GET"])
@role_required("patient")
def get_patient_appointments():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT a.*, d_user.name as doctor_name, dep.name as department_name, doc.specialization
        FROM appointments a
        JOIN patients p ON a.patient_id = p.id
        JOIN doctors doc ON a.doctor_id = doc.id
        JOIN users d_user ON doc.user_id = d_user.id
        LEFT JOIN departments dep ON doc.department_id = dep.id
        WHERE p.user_id = %s
        ORDER BY a.appointment_date DESC, a.appointment_time DESC
    """, (session["user_id"],))
    appointments = cur.fetchall()
    cur.close()
    conn.close()

    return jsonify({"appointments": [serialize_row(a) for a in appointments]})
