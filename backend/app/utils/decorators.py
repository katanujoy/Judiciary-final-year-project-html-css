# app/utils/decorators.py
from functools import wraps
from flask import jsonify
from flask_jwt_extended import get_jwt_identity
from app.models import User

def role_required(*required_roles):
    """
    Decorator to check if user has required role(s).
    
    Usage:
    @role_required('admin', 'judge')
    def some_function():
        ...
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            try:
                current_user_id = get_jwt_identity()
                user = User.query.get(int(current_user_id))
                
                if not user:
                    return jsonify({'error': 'User not found'}), 404
                
                if user.role not in required_roles:
                    return jsonify({'error': f'Access denied. Required roles: {required_roles}'}), 403
                
                return f(*args, **kwargs)
            except Exception as e:
                return jsonify({'error': 'Authorization check failed', 'details': str(e)}), 500
        
        return decorated_function
    return decorator