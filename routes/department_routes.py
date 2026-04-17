from flask import Blueprint, request, jsonify
from auth import role_required
from db import get_connection

department_bp = Blueprint("department", __name__)

@department_bp.route("/api/departments", methods=["GET"])
def get_departments():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM departments ORDER BY name")
    departments = cur.fetchall()
    cur.close()
    conn.close()
    return jsonify({"departments": departments})

@department_bp.route("/api/departments", methods=["POST"])
@role_required("admin")
def create_department():
    data = request.get_json()
    name = data.get("name")
    description = data.get("description")

    if not name:
        return jsonify({"error": "Department name is required"}), 400

    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO departments (name, description) VALUES (%s, %s) RETURNING id",
            (name, description)
        )
        dept_id = cur.fetchone()["id"]
        conn.commit()
        cur.close()
        conn.close()
        return jsonify({"message": "Department created", "id": dept_id}), 201
    except Exception as e:
        if "duplicate" in str(e).lower() or "1062" in str(e):
            return jsonify({"error": "Department already exists"}), 409
        return jsonify({"error": str(e)}), 500

@department_bp.route("/api/departments/<int:dept_id>", methods=["DELETE"])
@role_required("admin")
def delete_department(dept_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM departments WHERE id = %s", (dept_id,))
    if cur.rowcount == 0:
        cur.close()
        conn.close()
        return jsonify({"error": "Department not found"}), 404
    conn.commit()
    cur.close()
    conn.close()
    return jsonify({"message": "Department deleted"})
