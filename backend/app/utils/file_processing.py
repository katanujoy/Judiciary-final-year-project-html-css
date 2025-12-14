# app/utils/file_processing.py
import os
import uuid
from flask import current_app
from werkzeug.utils import secure_filename
import shutil
from datetime import datetime

def save_uploaded_file(file, case_id, user_id):
    """Save uploaded file with proper naming and structure."""
    # Create directory structure: uploads/case_{id}/user_{id}/
    case_dir = os.path.join(
        current_app.config['UPLOAD_FOLDER'],
        f'case_{case_id}'
    )
    user_dir = os.path.join(case_dir, f'user_{user_id}')
    
    os.makedirs(user_dir, exist_ok=True)
    
    # Generate unique filename
    original_filename = secure_filename(file.filename)
    file_extension = os.path.splitext(original_filename)[1]
    unique_filename = f"{uuid.uuid4().hex}{file_extension}"
    
    # Save file
    file_path = os.path.join(user_dir, unique_filename)
    file.save(file_path)
    
    # Get file size
    file_size = os.path.getsize(file_path)
    
    return file_path, file_size

def process_ocr(file_path):
    """Process OCR on uploaded file (simplified version)."""
    # In production, you would use Tesseract, Azure OCR, Google Vision, etc.
    # This is a simplified version
    try:
        # For PDF files, you'd use PyPDF2 or similar
        # For images, you'd use PIL + Tesseract
        return "OCR text would appear here"
    except Exception as e:
        print(f"OCR processing failed: {e}")
        return None

def get_file_size_readable(size_bytes):
    """Convert bytes to human readable format."""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.2f} TB"