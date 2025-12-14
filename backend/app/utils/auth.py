# app/utils/auth.py
import bcrypt

def hash_password(password):
    """Hash a password for storing."""
    if not password:
        raise ValueError("Password cannot be empty")
    
    try:
        salt = bcrypt.gensalt()
        pwd_hash = bcrypt.hashpw(password.encode('utf-8'), salt)
        return pwd_hash.decode('utf-8')
    except Exception as e:
        raise ValueError(f"Password hashing failed: {str(e)}")

def verify_password(password, hashed_password):
    """Verify a stored password against one provided by user."""
    if not password or not hashed_password:
        return False
    
    try:
        return bcrypt.checkpw(
            password.encode('utf-8'), 
            hashed_password.encode('utf-8')
        )
    except Exception:
        return False