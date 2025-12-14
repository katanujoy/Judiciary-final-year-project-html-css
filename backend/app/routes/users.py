from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.models import User, db, AuditLog
from app.utils.auth import hash_password

users_bp = Blueprint('users', __name__)

# ---------------------------------------------------------
# GET ALL USERS (Admin only)
# ---------------------------------------------------------
@users_bp.route('', methods=['GET'])
@jwt_required()
def get_all_users():
    current_user_id = get_jwt_identity()
    current_user = User.query.get(current_user_id)
    
    if not current_user or current_user.role != 'admin':
        return jsonify({'error': 'Admin access required'}), 403
    
    # Get query parameters
    search = request.args.get('search', '')
    role = request.args.get('role', '')
    status = request.args.get('status', '')
    
    query = User.query
    
    # Apply filters
    if search:
        query = query.filter(
            (User.full_name.ilike(f'%{search}%')) |
            (User.email.ilike(f'%{search}%')) |
            (User.employee_id.ilike(f'%{search}%'))
        )
    
    if role:
        query = query.filter_by(role=role)
    
    if status == 'active':
        query = query.filter_by(is_active=True)
    elif status == 'inactive':
        query = query.filter_by(is_active=False)
    elif status == 'pending':
        query = query.filter_by(is_approved=False)
    elif status == 'approved':
        query = query.filter_by(is_approved=True)
    
    # Pagination
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    
    users = query.order_by(User.created_at.desc())\
        .paginate(page=page, per_page=per_page, error_out=False)
    
    return jsonify({
        'users': [user.to_dict() for user in users.items],
        'total': users.total,
        'pages': users.pages,
        'current_page': page
    }), 200


# ---------------------------------------------------------
# GET PENDING USERS
# ---------------------------------------------------------
@users_bp.route('/pending', methods=['GET'])
@jwt_required()
def get_pending_users():
    current_user_id = get_jwt_identity()
    current_user = User.query.get(current_user_id)
    
    if not current_user or current_user.role != 'admin':
        return jsonify({'error': 'Admin access required'}), 403
    
    # Get pending users
    pending_users = User.query.filter_by(is_approved=False).all()
    
    return jsonify({
        'users': [user.to_dict() for user in pending_users],
        'count': len(pending_users)
    }), 200


# ---------------------------------------------------------
# APPROVE USER
# ---------------------------------------------------------
@users_bp.route('/<int:user_id>/approve', methods=['POST'])
@jwt_required()
def approve_user(user_id):
    current_user_id = get_jwt_identity()
    current_user = User.query.get(current_user_id)
    
    if not current_user or current_user.role != 'admin':
        return jsonify({'error': 'Admin access required'}), 403
    
    user = User.query.get(user_id)
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    user.is_approved = True
    user.is_active = True
    
    # Audit log
    audit_log = AuditLog(
        user_id=current_user_id,
        action='user_approve',
        resource_type='user',
        resource_id=user_id,
        details=f'Approved user {user.email} ({user.role})'
    )
    
    db.session.add(audit_log)
    db.session.commit()
    
    return jsonify({
        'message': 'User approved successfully',
        'user': user.to_dict()
    }), 200


# ---------------------------------------------------------
# REJECT USER
# ---------------------------------------------------------
@users_bp.route('/<int:user_id>/reject', methods=['POST'])
@jwt_required()
def reject_user(user_id):
    current_user_id = get_jwt_identity()
    current_user = User.query.get(current_user_id)
    
    if not current_user or current_user.role != 'admin':
        return jsonify({'error': 'Admin access required'}), 403
    
    user = User.query.get(user_id)
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    data = request.get_json() or {}
    reason = data.get('reason', 'No reason provided')
    
    # Audit log before deletion
    audit_log = AuditLog(
        user_id=current_user_id,
        action='user_reject',
        resource_type='user',
        resource_id=user_id,
        details=f'Rejected user {user.email}: {reason}'
    )
    
    db.session.add(audit_log)
    db.session.delete(user)
    db.session.commit()
    
    return jsonify({'message': 'User rejected and deleted'}), 200


# ---------------------------------------------------------
# RESET PASSWORD
# ---------------------------------------------------------
@users_bp.route('/<int:user_id>/reset-password', methods=['POST'])
@jwt_required()
def reset_user_password(user_id):
    current_user_id = get_jwt_identity()
    current_user = User.query.get(current_user_id)
    
    if not current_user:
        return jsonify({'error': 'Unauthorized'}), 401
    
    # Users can reset their own password, admins can reset any
    if current_user.id != user_id and current_user.role != 'admin':
        return jsonify({'error': 'Insufficient permissions'}), 403
    
    data = request.get_json() or {}
    new_password = data.get('new_password')
    
    if not new_password or len(new_password) < 8:
        return jsonify({'error': 'New password must be at least 8 characters'}), 400
    
    user = User.query.get(user_id)
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    user.password_hash = hash_password(new_password)
    
    # Audit log
    audit_log = AuditLog(
        user_id=current_user_id,
        action='password_reset',
        resource_type='user',
        resource_id=user_id,
        details='Password reset by ' + ('self' if current_user.id == user_id else 'admin')
    )
    
    db.session.add(audit_log)
    db.session.commit()
    
    return jsonify({'message': 'Password reset successfully'}), 200


# ---------------------------------------------------------
# UPDATE USER
# ---------------------------------------------------------
@users_bp.route('/<int:user_id>', methods=['PUT'])
@jwt_required()
def update_user(user_id):
    current_user_id = get_jwt_identity()
    current_user = User.query.get(current_user_id)
    
    if not current_user:
        return jsonify({'error': 'Unauthorized'}), 401
    
    # Users can update their own profile, admins can update any
    if current_user.id != user_id and current_user.role != 'admin':
        return jsonify({'error': 'Insufficient permissions'}), 403
    
    user = User.query.get(user_id)
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    data = request.get_json() or {}
    
    # Update allowed fields
    if 'full_name' in data:
        user.full_name = data['full_name']
    
    if 'court_station' in data:
        user.court_station = data['court_station']
    
    # Only admin can change role and active status
    if current_user.role == 'admin':
        if 'role' in data and data['role'] in ['judge', 'clerk', 'admin']:
            user.role = data['role']
        
        if 'is_active' in data:
            user.is_active = bool(data['is_active'])
    
    # Audit log
    audit_log = AuditLog(
        user_id=current_user_id,
        action='user_update',
        resource_type='user',
        resource_id=user_id,
        details='User profile updated'
    )
    
    db.session.add(audit_log)
    db.session.commit()
    
    return jsonify({
        'message': 'User updated successfully',
        'user': user.to_dict()
    }), 200


# ---------------------------------------------------------
# DEACTIVATE/ACTIVATE USER
# ---------------------------------------------------------
@users_bp.route('/<int:user_id>/toggle-active', methods=['POST'])
@jwt_required()
def toggle_user_active(user_id):
    current_user_id = get_jwt_identity()
    current_user = User.query.get(current_user_id)
    
    if not current_user or current_user.role != 'admin':
        return jsonify({'error': 'Admin access required'}), 403
    
    user = User.query.get(user_id)
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    user.is_active = not user.is_active
    action = 'activated' if user.is_active else 'deactivated'
    
    # Audit log
    audit_log = AuditLog(
        user_id=current_user_id,
        action='user_toggle_active',
        resource_type='user',
        resource_id=user_id,
        details=f'User {action}: {user.email}'
    )
    
    db.session.add(audit_log)
    db.session.commit()
    
    return jsonify({
        'message': f'User {action} successfully',
        'user': user.to_dict()
    }), 200


# ---------------------------------------------------------
# GET USER STATISTICS
# ---------------------------------------------------------
@users_bp.route('/statistics', methods=['GET'])
@jwt_required()
def get_user_statistics():
    current_user_id = get_jwt_identity()
    current_user = User.query.get(current_user_id)
    
    if not current_user or current_user.role != 'admin':
        return jsonify({'error': 'Admin access required'}), 403
    
    total_users = User.query.count()
    active_users = User.query.filter_by(is_active=True).count()
    pending_users = User.query.filter_by(is_approved=False).count()
    
    # Count by role
    judges = User.query.filter_by(role='judge', is_active=True).count()
    clerks = User.query.filter_by(role='clerk', is_active=True).count()
    admins = User.query.filter_by(role='admin', is_active=True).count()
    
    # Recent registrations (last 7 days)
    from datetime import datetime, timedelta
    week_ago = datetime.utcnow() - timedelta(days=7)
    recent_users = User.query.filter(User.created_at >= week_ago).count()
    
    return jsonify({
        'total': total_users,
        'active': active_users,
        'pending': pending_users,
        'by_role': {
            'judges': judges,
            'clerks': clerks,
            'admins': admins
        },
        'recent_week': recent_users
    }), 200