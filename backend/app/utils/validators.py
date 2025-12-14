# app/utils/validators.py
import os
import re
from config import Config

def validate_email_domain(email):
    """Validate email domain is from judiciary."""
    if not email or '@' not in email:
        return False
    
    domain = email.split('@')[1].lower()
    allowed_domains = Config.ALLOWED_EMAIL_DOMAINS
    
    return any(domain.endswith(allowed_domain) for allowed_domain in allowed_domains)

def validate_file_type(filename):
    """Check if file extension is allowed."""
    if not filename:
        return False
    
    allowed_extensions = Config.ALLOWED_EXTENSIONS
    file_extension = filename.rsplit('.', 1)[1].lower() if '.' in filename else ''
    
    return file_extension in allowed_extensions

def validate_password_strength(password):
    """Check if password meets security requirements."""
    if len(password) < 8:
        return False, "Password must be at least 8 characters long"
    
    if not re.search(r'[A-Z]', password):
        return False, "Password must contain at least one uppercase letter"
    
    if not re.search(r'[a-z]', password):
        return False, "Password must contain at least one lowercase letter"
    
    if not re.search(r'\d', password):
        return False, "Password must contain at least one number"
    
    return True, "Password is strong"

def validate_case_number(case_number):
    """Validate case number format (e.g., CR-2024-001)."""
    pattern = r'^[A-Z]{2,4}-\d{4}-\d{3,5}$'
    return bool(re.match(pattern, case_number))