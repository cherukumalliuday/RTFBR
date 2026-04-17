import os
from flask import Flask, send_from_directory
from flask_cors import CORS
from db import init_db
from routes.auth_routes import auth_bp
from routes.patient_routes import patient_bp
from routes.doctor_routes import doctor_bp
from routes.appointment_routes import appointment_bp
from routes.queue_routes import queue_bp
from routes.admin_routes import admin_bp
from routes.department_routes import department_bp

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FRONTEND_DIR = os.path.join(BASE_DIR, "frontend")

app = Flask(__name__, static_folder=FRONTEND_DIR, static_url_path="")
app.secret_key = os.environ.get("SESSION_SECRET", "mediqueue-dev-secret")

CORS(app, supports_credentials=True, origins="*")

app.register_blueprint(auth_bp)
app.register_blueprint(patient_bp)
app.register_blueprint(doctor_bp)
app.register_blueprint(appointment_bp)
app.register_blueprint(queue_bp)
app.register_blueprint(admin_bp)
app.register_blueprint(department_bp)

@app.route("/")
def index():
    return send_from_directory(FRONTEND_DIR, "index.html")

@app.route("/<path:path>")
def serve_static(path):
    return send_from_directory(FRONTEND_DIR, path)

try:
    init_db()
except Exception as e:
    print(f"DB init warning: {e}")

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
