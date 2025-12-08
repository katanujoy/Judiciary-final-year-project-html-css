# app/routes/auth.py

from flask import Blueprint, request, jsonify
from flask_jwt_extended import (
    create_access_token, jwt_required,
    get_jwt_identity
)
from app.models import User, db, AuditLog
from app.utils.auth import hash_password, verify_password
from app.utils.validators import validate_email_domain
from datetime import datetime

auth_bp = Blueprint("auth", __name__)


# -------------------------------------------------------
# LOGIN
# -------------------------------------------------------
@auth_bp.route("/login", methods=["POST"])
def login():
    try:
        data = request.get_json() or {}

        email = data.get("email")
        password = data.get("password")
        role = data.get("role")

        if not all([email, password, role]):
            return jsonify({"error": "All fields are required"}), 400

        user = User.query.filter_by(email=email, role=role).first()

        if not user:
            return jsonify({"error": "User not found"}), 404

        if not verify_password(password, user.password_hash):
            return jsonify({"error": "Invalid email or password"}), 401

        if not user.is_approved:
            return jsonify({"error": "Account pending administrator approval"}), 403

        if not user.is_active:
            return jsonify({"error": "Account deactivated"}), 403

        # Update login timestamp
        user.last_login = datetime.utcnow()

        # Create JWT
        access_token = create_access_token(
            identity=str(user.id),
            additional_claims={
                "email": user.email,
                "role": user.role,
                "name": user.full_name,
            },
        )

        # Log activity
        audit = AuditLog(
            user_id=user.id,
            action="login",
            details="User logged in",
            ip_address=request.remote_addr,
            user_agent=request.user_agent.string
        )
        db.session.add_all([user, audit])
        db.session.commit()

        return jsonify({
            "access_token": access_token,
            "message": "Login successful",
            "user": user.to_dict()
        }), 200

    except Exception:
        db.session.rollback()
        return jsonify({"error": "Unexpected server error during login"}), 500



# -------------------------------------------------------
# REGISTER
# -------------------------------------------------------
@auth_bp.route("/register", methods=["POST"])
def register():
    try:
        data = request.get_json() or {}

        required = [
            "email", "password", "full_name",
            "employee_id", "role", "court_station"
        ]

        if not all(field in data for field in required):
            return jsonify({"error": "All fields are required"}), 400

        email = data["email"]

        if not validate_email_domain(email):
            return jsonify({"error": "Only official judiciary email allowed"}), 400

        # Prevent duplicates
        if User.query.filter_by(email=email).first():
            return jsonify({"error": "Email already registered"}), 409

        if User.query.filter_by(employee_id=data["employee_id"]).first():
            return jsonify({"error": "Employee ID already registered"}), 409

        allowed_roles = ["judge", "clerk", "admin", "registrar"]

        if data["role"] not in allowed_roles:
            return jsonify({
                "error": f"Invalid role. Allowed roles: {', '.join(allowed_roles)}"
            }), 400

        user = User(
            email=email,
            password_hash=hash_password(data["password"]),
            full_name=data["full_name"],
            employee_id=data["employee_id"],
            role=data["role"],
            court_station=data["court_station"],
            is_active=True,
            is_approved=False
        )

        db.session.add(user)

        # Register audit
        audit = AuditLog(
            action="registration",
            user_id=user.id,
            details=f"New registration for {email} as {data['role']}",
            ip_address=request.remote_addr,
            user_agent=request.user_agent.string
        )
        db.session.add(audit)

        db.session.commit()

        return jsonify({
            "message": "Registration submitted. Awaiting administrator approval.",
            "user_id": user.id
        }), 201

    except Exception:
        db.session.rollback()
        return jsonify({"error": "Unexpected server error during registration"}), 500



# -------------------------------------------------------
# GET CURRENT USER
# -------------------------------------------------------
@auth_bp.route("/me", methods=["GET"])
@jwt_required()
def get_current_user():
    try:
        user_id = get_jwt_identity()
        user = User.query.get(int(user_id))

        if not user:
            return jsonify({"error": "User does not exist"}), 404

        return jsonify({"user": user.to_dict()}), 200

    except Exception:
        return jsonify({"error": "Failed to fetch user"}), 500



# -------------------------------------------------------
# CHANGE PASSWORD
# -------------------------------------------------------
@auth_bp.route("/change-password", methods=["POST"])
@jwt_required()
def change_password():
    try:
        user_id = get_jwt_identity()
        user = User.query.get(int(user_id))

        data = request.get_json() or {}

        old_password = data.get("current_password")
        new_password = data.get("new_password")

        if not all([old_password, new_password]):
            return jsonify({"error": "Both passwords required"}), 400

        if not verify_password(old_password, user.password_hash):
            return jsonify({"error": "Current password is incorrect"}), 401

        user.password_hash = hash_password(new_password)

        audit = AuditLog(
            user_id=user.id,
            action="password_change",
            details="Password updated successfully",
            ip_address=request.remote_addr
        )

        db.session.add_all([user, audit])
        db.session.commit()

        return jsonify({"message": "Password updated successfully"}), 200

    except Exception:
        db.session.rollback()
        return jsonify({"error": "Failed to change password"}), 500



# -------------------------------------------------------
# LOGOUT
# -------------------------------------------------------
@auth_bp.route("/logout", methods=["POST"])
@jwt_required()
def logout():
    try:
        user_id = get_jwt_identity()

        audit = AuditLog(
            user_id=int(user_id),
            action="logout",
            details="User logged out",
            ip_address=request.remote_addr,
            user_agent=request.user_agent.string
        )

        db.session.add(audit)
        db.session.commit()

        return jsonify({"message": "Logout successful"}), 200

    except Exception:
        db.session.rollback()
        return jsonify({"error": "Logout failed"}), 500
