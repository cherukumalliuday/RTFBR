from flask import Blueprint, request, jsonify, session
from auth import login_required, role_required
from db import get_connection, serialize_row
from datetime import date

queue_bp = Blueprint("queue", __name__)

@queue_bp.route("/api/queue/doctor", methods=["GET"])
@role_required("doctor")
def get_doctor_queue():
    queue_date = request.args.get("date", date.today().isoformat())

    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT q.*, p_user.name as patient_name, a.reason, a.appointment_time
        FROM queue q
        JOIN patients p ON q.patient_id = p.id
        JOIN users p_user ON p.user_id = p_user.id
        JOIN appointments a ON q.appointment_id = a.id
        JOIN doctors doc ON q.doctor_id = doc.id
        WHERE doc.user_id = %s AND q.queue_date = %s
        ORDER BY q.queue_number
    """, (session["user_id"], queue_date))
    queue_items = cur.fetchall()
    cur.close()
    conn.close()

    return jsonify({"queue": [serialize_row(item) for item in queue_items]})

@queue_bp.route("/api/queue/patient", methods=["GET"])
@role_required("patient")
def get_patient_queue_status():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT q.*, d_user.name as doctor_name, doc.specialization,
        a.appointment_date, a.appointment_time
        FROM queue q
        JOIN doctors doc ON q.doctor_id = doc.id
        JOIN users d_user ON doc.user_id = d_user.id
        JOIN appointments a ON q.appointment_id = a.id
        JOIN patients p ON q.patient_id = p.id
        WHERE p.user_id = %s AND q.queue_date = CURRENT_DATE AND q.status IN ('waiting', 'in_progress')
        ORDER BY q.queue_number
    """, (session["user_id"],))
    queue_items = cur.fetchall()

    result = []
    for item in queue_items:
        cur.execute("""
            SELECT COUNT(*) as ahead
            FROM queue WHERE doctor_id = %s AND queue_date = %s
            AND status = 'waiting' AND queue_number < %s
        """, (item["doctor_id"], item["queue_date"], item["queue_number"]))
        ahead = cur.fetchone()["ahead"]

        row = serialize_row(item)
        row["patients_ahead"] = ahead
        result.append(row)

    cur.close()
    conn.close()
    return jsonify({"queue": result})

@queue_bp.route("/api/queue/<int:queue_id>/next", methods=["PUT"])
@role_required("doctor")
def call_next_patient(queue_id):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        UPDATE queue SET status = 'in_progress', start_time = NOW()
        WHERE id = %s AND doctor_id IN (SELECT id FROM doctors WHERE user_id = %s)
        AND status = 'waiting'
    """, (queue_id, session["user_id"]))

    if cur.rowcount == 0:
        cur.close()
        conn.close()
        return jsonify({"error": "Queue entry not found or already processed"}), 404

    conn.commit()
    cur.close()
    conn.close()
    return jsonify({"message": "Patient called"})

@queue_bp.route("/api/queue/<int:queue_id>/complete", methods=["PUT"])
@role_required("doctor")
def complete_patient(queue_id):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        UPDATE queue SET status = 'completed', end_time = NOW()
        WHERE id = %s AND doctor_id IN (SELECT id FROM doctors WHERE user_id = %s)
        AND status = 'in_progress'
    """, (queue_id, session["user_id"]))

    if cur.rowcount == 0:
        cur.close()
        conn.close()
        return jsonify({"error": "Queue entry not found"}), 404

    cur.execute("SELECT appointment_id FROM queue WHERE id = %s", (queue_id,))
    row = cur.fetchone()
    if row:
        cur.execute(
            "UPDATE appointments SET status = 'completed' WHERE id = %s",
            (row["appointment_id"],)
        )

    conn.commit()
    cur.close()
    conn.close()
    return jsonify({"message": "Patient visit completed"})

@queue_bp.route("/api/queue/<int:queue_id>/skip", methods=["PUT"])
@role_required("doctor")
def skip_patient(queue_id):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        UPDATE queue SET status = 'skipped'
        WHERE id = %s AND doctor_id IN (SELECT id FROM doctors WHERE user_id = %s)
        AND status = 'waiting'
    """, (queue_id, session["user_id"]))

    if cur.rowcount == 0:
        cur.close()
        conn.close()
        return jsonify({"error": "Queue entry not found"}), 404

    conn.commit()
    cur.close()
    conn.close()
    return jsonify({"message": "Patient skipped"})

@queue_bp.route("/api/queue/live/<int:doctor_id>", methods=["GET"])
def get_live_queue(doctor_id):
    queue_date = request.args.get("date", date.today().isoformat())

    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT q.queue_number, q.status, d_user.name as doctor_name
        FROM queue q
        JOIN doctors doc ON q.doctor_id = doc.id
        JOIN users d_user ON doc.user_id = d_user.id
        WHERE q.doctor_id = %s AND q.queue_date = %s
        AND q.status IN ('waiting', 'in_progress')
        ORDER BY q.queue_number
    """, (doctor_id, queue_date))
    queue_items = cur.fetchall()

    cur.execute("""
        SELECT queue_number FROM queue
        WHERE doctor_id = %s AND queue_date = %s AND status = 'in_progress'
    """, (doctor_id, queue_date))
    current = cur.fetchone()

    cur.close()
    conn.close()

    return jsonify({
        "queue": queue_items,
        "current_number": current["queue_number"] if current else None,
        "total_waiting": len([q for q in queue_items if q["status"] == "waiting"])
    })
