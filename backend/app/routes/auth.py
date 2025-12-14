# app/routes/auth.py
from flask import Blueprint, request, jsonify
from flask_jwt_extended import (
    create_access_token, jwt_required,
    get_jwt_identity
)
from app.models import User, db, AuditLog
from app.utils.auth import hash_password, verify_password
from app.utils.validators import validate_email_domain
from datetime import datetime, timedelta

auth_bp = Blueprint("auth", __name__)


# -----------------------------
# LOGIN
# -----------------------------
@auth_bp.route("/login", methods=["POST"])
def login():
    try:
        data = request.get_json() or {}
        email = data.get("email", "").strip()
        password = data.get("password", "")

        if not email or not password:
            return jsonify({"error": "Email and password are required"}), 400

        user = User.query.filter_by(email=email).first()
        if not user or not verify_password(password, user.password_hash):
            return jsonify({"error": "Invalid email or password"}), 401

        if not user.is_approved:
            return jsonify({"error": "Account pending administrator approval"}), 403

        if not user.is_active:
            return jsonify({"error": "Account deactivated"}), 403

        # Update last login
        user.last_login = datetime.utcnow()
        db.session.add(user)

        # Create JWT token with expiration
        access_token = create_access_token(
            identity=str(user.id),
            additional_claims={
                "email": user.email,
                "role": user.role,
                "name": user.full_name,
            },
            expires_delta=timedelta(hours=24)
        )

        # Audit log
        audit = AuditLog(
            user_id=user.id,
            action="login",
            details="User logged in successfully",
            ip_address=request.remote_addr or 'unknown',
            user_agent=(request.user_agent.string if request.user_agent else 'unknown')
        )
        db.session.add(audit)
        db.session.commit()

        return jsonify({
            "access_token": access_token,
            "message": "Login successful",
            "user": user.to_dict()
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "Login failed", "details": str(e)}), 500


# -----------------------------
# REGISTER
# -----------------------------
@auth_bp.route("/register", methods=["POST"])
def register():
    try:
        data = request.get_json() or {}

        required_fields = ["email", "password", "full_name", "employee_id", "role", "court_station"]
        missing_fields = [field for field in required_fields if not data.get(field)]
        
        if missing_fields:
            return jsonify({"error": f"Missing required fields: {', '.join(missing_fields)}"}), 400

        email = data["email"].strip()
        password = data["password"]
        full_name = data["full_name"].strip()
        employee_id = data["employee_id"].strip()
        role = data["role"].strip().lower()
        court_station = data["court_station"].strip()

        # Validate email domain
        if not validate_email_domain(email):
            return jsonify({"error": "Only official judiciary email domains are allowed"}), 400

        # Check password strength
        if len(password) < 8:
            return jsonify({"error": "Password must be at least 8 characters long"}), 400

        # Check if email already exists
        if User.query.filter_by(email=email).first():
            return jsonify({"error": "Email already registered"}), 409
        
        # Check if employee ID already exists
        if User.query.filter_by(employee_id=employee_id).first():
            return jsonify({"error": "Employee ID already registered"}), 409

        # Validate role
        allowed_roles = ["judge", "clerk", "admin", "registrar"]
        if role not in allowed_roles:
            return jsonify({"error": f"Invalid role. Allowed roles: {', '.join(allowed_roles)}"}), 400

        # Create new user
        user = User(
            email=email,
            password_hash=hash_password(password),
            full_name=full_name,
            employee_id=employee_id,
            role=role,
            court_station=court_station,
            is_active=True,
            is_approved=(role == "admin")  # Auto-approve admins
        )
        
        db.session.add(user)
        db.session.flush()  # Get user ID before commit

        # Audit log
        audit = AuditLog(
            user_id=user.id,
            action="registration",
            details=f"New registration for {email} as {role}",
            ip_address=request.remote_addr or 'unknown',
            user_agent=(request.user_agent.string if request.user_agent else 'unknown')
        )
        db.session.add(audit)
        db.session.commit()

        # Auto-login for admins
        if role == "admin":
            access_token = create_access_token(
                identity=str(user.id),
                additional_claims={
                    "email": user.email,
                    "role": user.role,
                    "name": user.full_name,
                }
            )
            
            return jsonify({
                "message": "Admin account created and automatically approved",
                "access_token": access_token,
                "user": user.to_dict()
            }), 201
        else:
            return jsonify({
                "message": "Registration submitted. Awaiting administrator approval.",
                "user_id": user.id
            }), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "Registration failed", "details": str(e)}), 500


# -----------------------------
# GET CURRENT USER
# -----------------------------
@auth_bp.route("/me", methods=["GET"])
@jwt_required()
def get_current_user():
    try:
        user_id = get_jwt_identity()
        user = User.query.get(int(user_id))
        
        if not user:
            return jsonify({"error": "User not found"}), 404

        return jsonify({"user": user.to_dict()}), 200

    except Exception as e:
        return jsonify({"error": "Failed to fetch user profile", "details": str(e)}), 500


# -----------------------------
# CHANGE PASSWORD
# -----------------------------
@auth_bp.route("/change-password", methods=["POST"])
@jwt_required()
def change_password():
    try:
        user_id = get_jwt_identity()
        user = User.query.get(int(user_id))
        
        if not user:
            return jsonify({"error": "User not found"}), 404

        data = request.get_json() or {}
        old_password = data.get("current_password", "")
        new_password = data.get("new_password", "")
        confirm_password = data.get("confirm_password", "")

        # Validation
        if not old_password or not new_password:
            return jsonify({"error": "Current and new passwords are required"}), 400

        if new_password != confirm_password:
            return jsonify({"error": "New passwords do not match"}), 400

        if len(new_password) < 8:
            return jsonify({"error": "New password must be at least 8 characters long"}), 400

        if not verify_password(old_password, user.password_hash):
            return jsonify({"error": "Current password is incorrect"}), 401

        if verify_password(new_password, user.password_hash):
            return jsonify({"error": "New password cannot be the same as current password"}), 400

        # Update password
        user.password_hash = hash_password(new_password)
        db.session.add(user)

        # Audit log
        audit = AuditLog(
            user_id=user.id,
            action="password_change",
            details="Password changed successfully",
            ip_address=request.remote_addr or 'unknown'
        )
        db.session.add(audit)
        db.session.commit()

        return jsonify({"message": "Password updated successfully"}), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "Failed to change password", "details": str(e)}), 500


# -----------------------------
# LOGOUT
# -----------------------------
@auth_bp.route("/logout", methods=["POST"])
@jwt_required()
def logout():
    try:
        user_id = get_jwt_identity()
        user = User.query.get(int(user_id))
        
        if not user:
            return jsonify({"error": "User not found"}), 404

        audit = AuditLog(
            user_id=user.id,
            action="logout",
            details="User logged out successfully",
            ip_address=request.remote_addr or 'unknown',
            user_agent=(request.user_agent.string if request.user_agent else 'unknown')
        )
        db.session.add(audit)
        db.session.commit()
        
        return jsonify({"message": "Logout successful"}), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "Logout failed", "details": str(e)}), 500


# -----------------------------
# REFRESH TOKEN (Optional)
# -----------------------------
@auth_bp.route("/refresh", methods=["POST"])
@jwt_required(refresh=True)
def refresh_token():
    try:
        user_id = get_jwt_identity()
        user = User.query.get(int(user_id))
        
        if not user:
            return jsonify({"error": "User not found"}), 404

        # Create new access token
        access_token = create_access_token(
            identity=str(user.id),
            additional_claims={
                "email": user.email,
                "role": user.role,
                "name": user.full_name,
            }
        )

        return jsonify({
            "access_token": access_token,
            "message": "Token refreshed successfully"
        }), 200

    except Exception as e:
        return jsonify({"error": "Token refresh failed", "details": str(e)}), 500


# -----------------------------
# CHECK EMAIL AVAILABILITY
# -----------------------------
@auth_bp.route("/check-email", methods=["POST"])
def check_email():
    try:
        data = request.get_json() or {}
        email = data.get("email", "").strip()
        
        if not email:
            return jsonify({"error": "Email is required"}), 400

        exists = User.query.filter_by(email=email).first() is not None
        
        return jsonify({
            "email": email,
            "available": not exists,
            "message": "Email already registered" if exists else "Email is available"
        }), 200

    except Exception as e:
        return jsonify({"error": "Check failed", "details": str(e)}), 500


# -----------------------------
# FORGOT PASSWORD (Simplified - would need email service)
# -----------------------------
@auth_bp.route("/forgot-password", methods=["POST"])
def forgot_password():
    try:
        data = request.get_json() or {}
        email = data.get("email", "").strip()
        
        if not email:
            return jsonify({"error": "Email is required"}), 400

        user = User.query.filter_by(email=email).first()
        if not user:
            # Return success even if email doesn't exist (security best practice)
            return jsonify({
                "message": "If your email is registered, you will receive a password reset link"
            }), 200

        # In production, you would:
        # 1. Generate a reset token
        # 2. Send email with reset link
        # 3. Store token in database with expiration
        
        audit = AuditLog(
            user_id=user.id,
            action="password_reset_request",
            details="Password reset requested",
            ip_address=request.remote_addr or 'unknown'
        )
        db.session.add(audit)
        db.session.commit()

        return jsonify({
            "message": "If your email is registered, you will receive a password reset link"
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "Password reset request failed", "details": str(e)}), 500