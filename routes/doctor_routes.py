from flask import Blueprint, request, jsonify, session
from auth import login_required, role_required
from db import get_connection, serialize_row

doctor_bp = Blueprint("doctor", __name__)

@doctor_bp.route("/api/doctors", methods=["GET"])
def get_all_doctors():
    department_id = request.args.get("department_id")
    conn = get_connection()
    cur = conn.cursor()

    query = """
        SELECT doc.id, u.name, doc.specialization, doc.qualification,
        doc.experience_years, doc.available, dep.name as department_name
        FROM doctors doc
        JOIN users u ON doc.user_id = u.id
        LEFT JOIN departments dep ON doc.department_id = dep.id
        WHERE doc.available = TRUE
    """
    params = []
    if department_id:
        query += " AND doc.department_id = %s"
        params.append(department_id)

    query += " ORDER BY u.name"
    cur.execute(query, params)
    doctors = cur.fetchall()
    cur.close()
    conn.close()

    return jsonify({"doctors": doctors})

@doctor_bp.route("/api/doctors/profile", methods=["GET"])
@role_required("doctor")
def get_doctor_profile():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT doc.*, u.name, u.email, u.phone, dep.name as department_name
        FROM doctors doc
        JOIN users u ON doc.user_id = u.id
        LEFT JOIN departments dep ON doc.department_id = dep.id
        WHERE doc.user_id = %s
    """, (session["user_id"],))
    doctor = cur.fetchone()
    cur.close()
    conn.close()

    if not doctor:
        return jsonify({"error": "Doctor profile not found"}), 404

    return jsonify({"doctor": serialize_row(doctor)})

@doctor_bp.route("/api/doctors/profile", methods=["PUT"])
@role_required("doctor")
def update_doctor_profile():
    data = request.get_json()
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        UPDATE doctors SET specialization = %s, qualification = %s,
        experience_years = %s, available = %s, department_id = %s
        WHERE user_id = %s
    """, (
        data.get("specialization"), data.get("qualification"),
        data.get("experience_years"), data.get("available", True),
        data.get("department_id"), session["user_id"]
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

@doctor_bp.route("/api/doctors/appointments", methods=["GET"])
@role_required("doctor")
def get_doctor_appointments():
    status = request.args.get("status")
    date = request.args.get("date")

    conn = get_connection()
    cur = conn.cursor()

    query = """
        SELECT a.*, p_user.name as patient_name, p.gender, p.blood_group, p.date_of_birth
        FROM appointments a
        JOIN doctors doc ON a.doctor_id = doc.id
        JOIN patients p ON a.patient_id = p.id
        JOIN users p_user ON p.user_id = p_user.id
        WHERE doc.user_id = %s
    """
    params = [session["user_id"]]

    if status:
        query += " AND a.status = %s"
        params.append(status)
    if date:
        query += " AND a.appointment_date = %s"
        params.append(date)

    query += " ORDER BY a.appointment_date, a.appointment_time"
    cur.execute(query, params)
    appointments = cur.fetchall()
    cur.close()
    conn.close()

    return jsonify({"appointments": [serialize_row(a) for a in appointments]})

@doctor_bp.route("/api/doctors/appointments/<int:appointment_id>/status", methods=["PUT"])
@role_required("doctor")
def update_appointment_status(appointment_id):
    data = request.get_json()
    new_status = data.get("status")
    notes = data.get("notes")

    if new_status not in ("confirmed", "completed", "cancelled"):
        return jsonify({"error": "Invalid status"}), 400

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        UPDATE appointments SET status = %s, notes = %s
        WHERE id = %s AND doctor_id IN (SELECT id FROM doctors WHERE user_id = %s)
    """, (new_status, notes, appointment_id, session["user_id"]))

    if cur.rowcount == 0:
        cur.close()
        conn.close()
        return jsonify({"error": "Appointment not found"}), 404

    conn.commit()
    cur.close()
    conn.close()
    return jsonify({"message": "Appointment status updated"})
