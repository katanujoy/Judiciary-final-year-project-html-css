# app/routes/files.py
from flask import Blueprint, request, jsonify, send_file
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.models import CaseFile, Case, User, db, AuditLog
from app.utils.file_processing import save_uploaded_file, get_file_size_readable
from app.utils.validators import validate_file_type
import os
from datetime import datetime
from werkzeug.utils import secure_filename

files_bp = Blueprint('files', __name__)

@files_bp.route('/upload', methods=['POST'])
@jwt_required()
def upload_file():
    current_user_id = get_jwt_identity()
    current_user = User.query.get(current_user_id)
    
    if not current_user:
        return jsonify({'error': 'Invalid user'}), 401
    
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    
    file = request.files['file']
    case_id = request.form.get('case_id')
    document_type = request.form.get('document_type', 'other')
    description = request.form.get('description', '')
    enable_ocr = request.form.get('enable_ocr', 'true').lower() == 'true'
    
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    if not validate_file_type(file.filename):
        return jsonify({'error': 'Invalid file type'}), 400
    
    # Verify case exists and user has access
    case = Case.query.get(case_id)
    if not case:
        return jsonify({'error': 'Case not found'}), 404
    
    # Check permissions
    if current_user.role == 'judge' and case.judge_id != current_user_id:
        return jsonify({'error': 'Access denied to this case'}), 403
    
    # Save file
    try:
        file_path, file_size = save_uploaded_file(file, case_id, current_user_id)
        
        # Create file record
        case_file = CaseFile(
            filename=os.path.basename(file_path),
            original_filename=secure_filename(file.filename),
            file_path=file_path,
            file_size=file_size,
            file_type=file.content_type,
            document_type=document_type,
            case_id=case_id,
            uploaded_by_id=current_user_id
        )
        
        db.session.add(case_file)
        db.session.commit()
        
        # Simple OCR processing (simulated)
        if enable_ocr and file.content_type in ['application/pdf', 'image/jpeg', 'image/png']:
            case_file.ocr_text = "Simulated OCR text from document. In production, this would contain actual extracted text."
            case_file.is_ocr_processed = True
        
        # Audit log
        audit_log = AuditLog(
            user_id=current_user_id,
            action='file_upload',
            resource_type='case_file',
            resource_id=case_file.id,
            details=f'Uploaded {file.filename} ({get_file_size_readable(file_size)}) to case {case.case_number}'
        )
        db.session.add(audit_log)
        db.session.commit()
        
        return jsonify({
            'message': 'File uploaded successfully',
            'file_id': case_file.id,
            'filename': case_file.original_filename,
            'size': get_file_size_readable(file_size),
            'ocr_processing': enable_ocr,
            'file': case_file.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Upload failed: {str(e)}'}), 500

@files_bp.route('/<int:file_id>', methods=['GET'])
@jwt_required()
def get_file(file_id):
    current_user_id = get_jwt_identity()
    current_user = User.query.get(current_user_id)
    
    if not current_user:
        return jsonify({'error': 'Invalid user'}), 401
    
    case_file = CaseFile.query.get_or_404(file_id)
    case = Case.query.get(case_file.case_id)
    
    # Check permissions
    if current_user.role == 'judge' and case.judge_id != current_user_id:
        return jsonify({'error': 'Access denied'}), 403
    
    return jsonify({
        'file': case_file.to_dict(),
        'case': case.to_dict() if case else None
    }), 200

@files_bp.route('/<int:file_id>/download', methods=['GET'])
@jwt_required()
def download_file(file_id):
    current_user_id = get_jwt_identity()
    current_user = User.query.get(current_user_id)
    
    if not current_user:
        return jsonify({'error': 'Invalid user'}), 401
    
    case_file = CaseFile.query.get_or_404(file_id)
    case = Case.query.get(case_file.case_id)
    
    # Check permissions
    if current_user.role == 'judge' and case.judge_id != current_user_id:
        return jsonify({'error': 'Access denied'}), 403
    
    # Audit download
    audit_log = AuditLog(
        user_id=current_user_id,
        action='file_download',
        resource_type='case_file',
        resource_id=file_id,
        details=f'Downloaded {case_file.original_filename}'
    )
    db.session.add(audit_log)
    db.session.commit()
    
    return send_file(
        case_file.file_path,
        as_attachment=True,
        download_name=case_file.original_filename
    )

@files_bp.route('/<int:file_id>', methods=['DELETE'])
@jwt_required()
def delete_file(file_id):
    current_user_id = get_jwt_identity()
    current_user = User.query.get(current_user_id)
    
    if not current_user or current_user.role != 'admin':
        return jsonify({'error': 'Admin access required'}), 403
    
    case_file = CaseFile.query.get_or_404(file_id)
    
    # Delete physical file
    try:
        if os.path.exists(case_file.file_path):
            os.remove(case_file.file_path)
    except Exception as e:
        print(f"Warning: Could not delete file {case_file.file_path}: {e}")
    
    # Audit before deletion
    audit_log = AuditLog(
        user_id=current_user_id,
        action='file_delete',
        resource_type='case_file',
        resource_id=file_id,
        details=f'Deleted {case_file.original_filename}'
    )
    db.session.add(audit_log)
    
    db.session.delete(case_file)
    db.session.commit()
    
    return jsonify({'message': 'File deleted successfully'}), 200

@files_bp.route('/case/<int:case_id>', methods=['GET'])
@jwt_required()
def get_case_files(case_id):
    current_user_id = get_jwt_identity()
    current_user = User.query.get(current_user_id)
    
    if not current_user:
        return jsonify({'error': 'Invalid user'}), 401
    
    case = Case.query.get_or_404(case_id)
    
    # Check permissions
    if current_user.role == 'judge' and case.judge_id != current_user_id:
        return jsonify({'error': 'Access denied'}), 403
    
    files = CaseFile.query.filter_by(case_id=case_id)\
        .order_by(CaseFile.created_at.desc()).all()
    
    return jsonify({
        'files': [file.to_dict() for file in files],
        'total': len(files)
    }), 200

@files_bp.route('/recent', methods=['GET'])
@jwt_required()
def get_recent_files():
    current_user_id = get_jwt_identity()
    current_user = User.query.get(current_user_id)
    
    if not current_user:
        return jsonify({'error': 'Invalid user'}), 401
    
    # Base query
    query = CaseFile.query
    
    # Judges only see files from their cases
    if current_user.role == 'judge':
        query = query.join(Case).filter(Case.judge_id == current_user_id)
    
    recent_files = query.order_by(CaseFile.created_at.desc())\
        .limit(10)\
        .all()
    
    return jsonify({
        'files': [file.to_dict() for file in recent_files]
    }), 200