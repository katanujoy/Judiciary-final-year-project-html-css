from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.models import User, db, AuditLog
from app.utils.auth import hash_password

users_bp = Blueprint('users', __name__)

# Helper to safely get a user and return 404 if not found
def get_user_or_404(user_id):
    user = User.query.get(user_id)
    if not user:
        return None, jsonify({'error': 'User not found'}), 404
    return user, None, None

@users_bp.route('/users/pending', methods=['GET'])
@jwt_required()
def get_pending_users():
    current_user = User.query.get(get_jwt_identity())
    if not current_user or current_user.role != 'admin':
        return jsonify({'error': 'Admin access required'}), 403

    # Safely query users where role is valid
    valid_roles = ['admin', 'clerk', 'judge']
    pending_users = User.query.filter(
        User.is_approved == False,
        User.role.in_(valid_roles)  # avoid invalid enum errors
    ).all()

    return jsonify({'users': [user.to_dict() for user in pending_users]})


@users_bp.route('/users/<int:user_id>/approve', methods=['POST'])
@jwt_required()
def approve_user(user_id):
    current_user = User.query.get(get_jwt_identity())
    if not current_user or current_user.role != 'admin':
        return jsonify({'error': 'Admin access required'}), 403

    user, err_resp, status = get_user_or_404(user_id)
    if err_resp:
        return err_resp, status

    user.is_approved = True
    db.session.commit()

    # Audit log
    audit_log = AuditLog(
        user_id=current_user.id,
        action='user_approve',
        resource_type='user',
        resource_id=user.id,
        details=f'Approved user {user.email}'
    )
    db.session.add(audit_log)
    db.session.commit()

    return jsonify({'message': 'User approved successfully'})


@users_bp.route('/users/<int:user_id>/reset-password', methods=['POST'])
@jwt_required()
def reset_user_password(user_id):
    current_user = User.query.get(get_jwt_identity())
    if not current_user:
        return jsonify({'error': 'Unauthorized'}), 403

    # Users can reset their own password, admins can reset any
    if current_user.id != user_id and current_user.role != 'admin':
        return jsonify({'error': 'Insufficient permissions'}), 403

    data = request.get_json()
    new_password = data.get('new_password')
    if not new_password:
        return jsonify({'error': 'New password required'}), 400

    user, err_resp, status = get_user_or_404(user_id)
    if err_resp:
        return err_resp, status

    user.password_hash = hash_password(new_password)
    db.session.commit()

    # Audit log
    audit_log = AuditLog(
        user_id=current_user.id,
        action='password_reset',
        resource_type='user',
        resource_id=user.id,
        details='Password reset'
    )
    db.session.add(audit_log)
    db.session.commit()

    return jsonify({'message': 'Password reset successfully'})
