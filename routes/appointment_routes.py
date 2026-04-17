from flask import Blueprint, request, jsonify, session
from auth import login_required, role_required
from db import get_connection, serialize_row

appointment_bp = Blueprint("appointment", __name__)

@appointment_bp.route("/api/appointments", methods=["POST"])
@role_required("patient")
def book_appointment():
    data = request.get_json()
    doctor_id = data.get("doctor_id")
    appointment_date = data.get("appointment_date")
    appointment_time = data.get("appointment_time")
    reason = data.get("reason")

    if not all([doctor_id, appointment_date, appointment_time]):
        return jsonify({"error": "Doctor, date and time are required"}), 400

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("SELECT id FROM patients WHERE user_id = %s", (session["user_id"],))
    patient = cur.fetchone()
    if not patient:
        cur.close()
        conn.close()
        return jsonify({"error": "Patient profile not found"}), 404

    cur.execute("SELECT id, available FROM doctors WHERE id = %s", (doctor_id,))
    doctor = cur.fetchone()
    if not doctor:
        cur.close()
        conn.close()
        return jsonify({"error": "Doctor not found"}), 404
    if not doctor["available"]:
        cur.close()
        conn.close()
        return jsonify({"error": "Doctor is not available"}), 400

    cur.execute("""
        SELECT id FROM appointments
        WHERE doctor_id = %s AND appointment_date = %s AND appointment_time = %s
        AND status NOT IN ('cancelled')
    """, (doctor_id, appointment_date, appointment_time))
    if cur.fetchone():
        cur.close()
        conn.close()
        return jsonify({"error": "This time slot is already booked"}), 409

    cur.execute("""
        INSERT INTO appointments (patient_id, doctor_id, appointment_date, appointment_time, reason)
        VALUES (%s, %s, %s, %s, %s) RETURNING id
    """, (patient["id"], doctor_id, appointment_date, appointment_time, reason))
    appointment_id = cur.fetchone()["id"]

    cur.execute("""
        SELECT COALESCE(MAX(queue_number), 0) + 1 as next_number
        FROM queue WHERE doctor_id = %s AND queue_date = %s
    """, (doctor_id, appointment_date))
    queue_number = cur.fetchone()["next_number"]

    cur.execute("""
        INSERT INTO queue (appointment_id, doctor_id, patient_id, queue_number, queue_date)
        VALUES (%s, %s, %s, %s, %s)
    """, (appointment_id, doctor_id, patient["id"], queue_number, appointment_date))

    conn.commit()
    cur.close()
    conn.close()

    return jsonify({
        "message": "Appointment booked successfully",
        "appointment_id": appointment_id,
        "queue_number": queue_number
    }), 201

@appointment_bp.route("/api/appointments/<int:appointment_id>", methods=["GET"])
@login_required
def get_appointment(appointment_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT a.*, p_user.name as patient_name, d_user.name as doctor_name,
        doc.specialization, dep.name as department_name
        FROM appointments a
        JOIN patients p ON a.patient_id = p.id
        JOIN users p_user ON p.user_id = p_user.id
        JOIN doctors doc ON a.doctor_id = doc.id
        JOIN users d_user ON doc.user_id = d_user.id
        LEFT JOIN departments dep ON doc.department_id = dep.id
        WHERE a.id = %s
    """, (appointment_id,))
    appointment = cur.fetchone()
    cur.close()
    conn.close()

    if not appointment:
        return jsonify({"error": "Appointment not found"}), 404

    appointment = serialize_row(appointment)
    return jsonify({"appointment": appointment})

@appointment_bp.route("/api/appointments/<int:appointment_id>/cancel", methods=["PUT"])
@role_required("patient")
def cancel_appointment(appointment_id):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        UPDATE appointments SET status = 'cancelled'
        WHERE id = %s AND patient_id IN (SELECT id FROM patients WHERE user_id = %s)
        AND status = 'pending'
    """, (appointment_id, session["user_id"]))

    if cur.rowcount == 0:
        cur.close()
        conn.close()
        return jsonify({"error": "Appointment not found or cannot be cancelled"}), 404

    cur.execute("""
        UPDATE queue SET status = 'skipped' WHERE appointment_id = %s
    """, (appointment_id,))

    conn.commit()
    cur.close()
    conn.close()
    return jsonify({"message": "Appointment cancelled successfully"})
