from flask import Blueprint, request, jsonify, session
from auth import role_required
from db import get_connection, serialize_row

admin_bp = Blueprint("admin", __name__)

@admin_bp.route("/api/admin/stats", methods=["GET"])
@role_required("admin")
def get_stats():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("SELECT COUNT(*) as count FROM patients")
    total_patients = cur.fetchone()["count"]

    cur.execute("SELECT COUNT(*) as count FROM doctors")
    total_doctors = cur.fetchone()["count"]

    cur.execute("SELECT COUNT(*) as count FROM appointments WHERE appointment_date = CURRENT_DATE")
    today_appointments = cur.fetchone()["count"]

    cur.execute("SELECT COUNT(*) as count FROM queue WHERE queue_date = CURRENT_DATE AND status = 'waiting'")
    active_queue = cur.fetchone()["count"]

    cur.close()
    conn.close()

    return jsonify({
        "total_patients": total_patients,
        "total_doctors": total_doctors,
        "today_appointments": today_appointments,
        "active_queue": active_queue
    })

@admin_bp.route("/api/admin/doctors", methods=["GET"])
@role_required("admin")
def get_all_doctors_admin():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT doc.id, u.name, u.email, u.phone, doc.specialization,
        doc.qualification, doc.experience_years, doc.available, dep.name as department_name
        FROM doctors doc
        JOIN users u ON doc.user_id = u.id
        LEFT JOIN departments dep ON doc.department_id = dep.id
        ORDER BY u.name
    """)
    doctors = cur.fetchall()
    cur.close()
    conn.close()
    return jsonify({"doctors": [serialize_row(d) for d in doctors]})

@admin_bp.route("/api/admin/doctors/<int:doctor_id>", methods=["PUT"])
@role_required("admin")
def update_doctor(doctor_id):
    data = request.get_json()
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        UPDATE doctors SET department_id = %s, specialization = %s,
        qualification = %s, experience_years = %s, available = %s
        WHERE id = %s
    """, (
        data.get("department_id"), data.get("specialization"),
        data.get("qualification"), data.get("experience_years"),
        data.get("available", True), doctor_id
    ))

    conn.commit()
    cur.close()
    conn.close()
    return jsonify({"message": "Doctor updated"})

@admin_bp.route("/api/admin/doctors/<int:doctor_id>", methods=["DELETE"])
@role_required("admin")
def delete_doctor(doctor_id):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("SELECT user_id FROM doctors WHERE id = %s", (doctor_id,))
    doctor = cur.fetchone()
    if not doctor:
        cur.close()
        conn.close()
        return jsonify({"error": "Doctor not found"}), 404

    cur.execute("DELETE FROM users WHERE id = %s", (doctor["user_id"],))
    conn.commit()
    cur.close()
    conn.close()
    return jsonify({"message": "Doctor removed"})

@admin_bp.route("/api/admin/appointments", methods=["GET"])
@role_required("admin")
def get_all_appointments():
    date = request.args.get("date")
    status = request.args.get("status")

    conn = get_connection()
    cur = conn.cursor()

    query = """
        SELECT a.id, a.appointment_date, a.appointment_time, a.status,
        p_user.name as patient_name, d_user.name as doctor_name,
        dep.name as department_name, a.reason
        FROM appointments a
        JOIN patients p ON a.patient_id = p.id
        JOIN users p_user ON p.user_id = p_user.id
        JOIN doctors doc ON a.doctor_id = doc.id
        JOIN users d_user ON doc.user_id = d_user.id
        LEFT JOIN departments dep ON doc.department_id = dep.id
        WHERE 1=1
    """
    params = []

    if date:
        query += " AND a.appointment_date = %s"
        params.append(date)
    if status:
        query += " AND a.status = %s"
        params.append(status)

    query += " ORDER BY a.appointment_date DESC, a.appointment_time DESC"
    cur.execute(query, params)
    appointments = cur.fetchall()
    cur.close()
    conn.close()

    return jsonify({"appointments": [serialize_row(a) for a in appointments]})

@admin_bp.route("/api/admin/patients", methods=["GET"])
@role_required("admin")
def get_all_patients():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT p.id, u.name, u.email, u.phone, p.gender, p.blood_group,
        p.date_of_birth, u.created_at
        FROM patients p
        JOIN users u ON p.user_id = u.id
        ORDER BY u.name
    """)
    patients = cur.fetchall()
    cur.close()
    conn.close()
    return jsonify({"patients": [serialize_row(p) for p in patients]})

@admin_bp.route("/api/admin/queue", methods=["GET"])
@role_required("admin")
def get_all_queue():
    date = request.args.get("date")
    conn = get_connection()
    cur = conn.cursor()

    query = """
        SELECT q.*, p_user.name as patient_name, d_user.name as doctor_name,
        dep.name as department_name
        FROM queue q
        JOIN patients p ON q.patient_id = p.id
        JOIN users p_user ON p.user_id = p_user.id
        JOIN doctors doc ON q.doctor_id = doc.id
        JOIN users d_user ON doc.user_id = d_user.id
        LEFT JOIN departments dep ON doc.department_id = dep.id
        WHERE 1=1
    """
    params = []
    if date:
        query += " AND q.queue_date = %s"
        params.append(date)
    else:
        query += " AND q.queue_date = CURRENT_DATE"

    query += " ORDER BY q.queue_number"
    cur.execute(query, params)
    queue = cur.fetchall()
    cur.close()
    conn.close()

    return jsonify({"queue": [serialize_row(item) for item in queue]})
