# app/utils/__init__.py
from .auth import hash_password, verify_password
from .validators import validate_email_domain, validate_file_type, validate_password_strength
from .file_processing import save_uploaded_file, process_ocr, get_file_size_readable
from .decorators import role_required 

# Remove 'role_required' from the import since it doesn't exist