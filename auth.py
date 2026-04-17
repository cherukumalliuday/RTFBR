from functools import wraps
from flask import request, jsonify, session

def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if "user_id" not in session:
            return jsonify({"error": "Authentication required"}), 401
        return f(*args, **kwargs)
    return decorated

def role_required(*roles):
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            if "user_id" not in session:
                return jsonify({"error": "Authentication required"}), 401
            if session.get("role") not in roles:
                return jsonify({"error": "Access denied"}), 403
            return f(*args, **kwargs)
        return decorated
    return decorator
