# app/utils/auth.py
import bcrypt
from functools import wraps
from flask import jsonify, request
from flask_jwt_extended import verify_jwt_in_request, get_jwt

def hash_password(password):
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def verify_password(password, password_hash):
    return bcrypt.checkpw(password.encode('utf-8'), password_hash.encode('utf-8'))

def role_required(roles):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            verify_jwt_in_request()
            claims = get_jwt()
            if claims.get('role') not in roles:
                return jsonify({'error': 'Insufficient permissions'}), 403
            return f(*args, **kwargs)
        return decorated_function
    return decorator

# app/utils/validators.py
def validate_email_domain(email):
    allowed_domains = ['judiciary.go.ke', 'judiciary.ke']
    domain = email.split('@')[-1]
    return domain in allowed_domains

def validate_file_type(filename):
    allowed_extensions = {'pdf', 'jpg', 'jpeg', 'png', 'docx'}
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_extensions