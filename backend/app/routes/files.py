# app/routes/files.py
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.models import CaseFile, Case, User, db, AuditLog
from app.utils.file_processing import save_uploaded_file, process_ocr
from app.utils.validators import validate_file_type
import os

files_bp = Blueprint('files', __name__)

@files_bp.route('/upload', methods=['POST'])
@jwt_required()
def upload_file():
    current_user_id = get_jwt_identity()
    
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    
    file = request.files['file']
    case_id = request.form.get('case_id')
    document_type = request.form.get('document_type')
    enable_ocr = request.form.get('enable_ocr', 'true').lower() == 'true'
    
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    if not validate_file_type(file.filename):
        return jsonify({'error': 'Invalid file type'}), 400
    
    # Verify case exists and user has access
    case = Case.query.get(case_id)
    if not case:
        return jsonify({'error': 'Case not found'}), 404
    
    # Save file
    try:
        file_path, file_size = save_uploaded_file(file, case_id, current_user_id)
        
        # Create file record
        case_file = CaseFile(
            filename=os.path.basename(file_path),
            original_filename=file.filename,
            file_path=file_path,
            file_size=file_size,
            file_type=file.content_type,
            document_type=document_type,
            case_id=case_id,
            uploaded_by_id=current_user_id
        )
        
        db.session.add(case_file)
        db.session.commit()
        
        # Process OCR in background if enabled
        if enable_ocr and file.content_type in ['application/pdf', 'image/jpeg', 'image/png']:
            process_ocr.delay(case_file.id)
        
        # Audit log
        audit_log = AuditLog(
            user_id=current_user_id,
            action='file_upload',
            resource_type='case_file',
            resource_id=case_file.id,
            details=f'Uploaded {file.filename} to case {case.case_number}'
        )
        db.session.add(audit_log)
        db.session.commit()
        
        return jsonify({
            'message': 'File uploaded successfully',
            'file_id': case_file.id,
            'ocr_processing': enable_ocr
        }), 201
        
    except Exception as e:
        return jsonify({'error': f'Upload failed: {str(e)}'}), 500