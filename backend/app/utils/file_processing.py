import os
import uuid
from werkzeug.utils import secure_filename
from app import db
from app.models import CaseFile

def save_uploaded_file(file, case_id, user_id):
    """Save uploaded file to filesystem"""
    # Create upload directory if it doesn't exist
    upload_dir = f"uploads/case_{case_id}"
    os.makedirs(upload_dir, exist_ok=True)
    
    # Generate unique filename
    file_extension = file.filename.rsplit('.', 1)[1].lower()
    unique_filename = f"{uuid.uuid4().hex}.{file_extension}"
    file_path = os.path.join(upload_dir, unique_filename)
    
    # Save file
    file.save(file_path)
    file_size = os.path.getsize(file_path)
    
    return file_path, file_size

def get_file_extension(filename):
    """Get file extension from filename"""
    return filename.rsplit('.', 1)[1].lower() if '.' in filename else ''

def is_image_file(filename):
    """Check if file is an image"""
    image_extensions = {'jpg', 'jpeg', 'png', 'gif', 'bmp'}
    return get_file_extension(filename) in image_extensions

def is_pdf_file(filename):
    """Check if file is a PDF"""
    return get_file_extension(filename) == 'pdf'

def cleanup_orphaned_files():
    """Clean up files that don't have database records"""
    # Implementation for cleaning orphaned files
    pass

# === Stub for OCR to prevent import errors ===
def process_ocr(file_path):
    """Placeholder for OCR processing"""
    # TODO: implement OCR later
    return ""
