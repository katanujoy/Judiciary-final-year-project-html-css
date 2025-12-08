from app.utils.auth import hash_password, verify_password, role_required
from app.utils.validators import validate_email_domain, validate_file_type
from app.utils.file_processing import save_uploaded_file  # removed process_ocr
from app.utils.ocr import extract_text_from_image, extract_text_from_pdf
from app.utils.backup import create_backup  # remove restore_backup if not implemented

__all__ = [
    'hash_password', 'verify_password', 'role_required',
    'validate_email_domain', 'validate_file_type',
    'save_uploaded_file',
    'extract_text_from_image', 'extract_text_from_pdf',
    'create_backup'
]
