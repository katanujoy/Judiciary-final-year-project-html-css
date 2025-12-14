# app/routes/backup.py
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.models import Backup, AuditLog, db, CaseFile
from datetime import datetime
import os
import shutil
import zipfile
from config import Config

backup_bp = Blueprint('backup', __name__)

def create_backup(backup_id, backup_type='full', storage_location='local'):
    """Create a backup of the database and files."""
    try:
        backup = Backup.query.get(backup_id)
        if not backup:
            return
        
        # Create backup directory
        backup_timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
        backup_dir = os.path.join(Config.BACKUP_DIR, f'backup_{backup_timestamp}')
        os.makedirs(backup_dir, exist_ok=True)
        
        # Backup database (SQLite specific - for production use pg_dump or mysqldump)
        if os.path.exists('judiciary.db'):
            shutil.copy2('judiciary.db', os.path.join(backup_dir, 'database.db'))
        
        # Backup uploaded files
        files_dir = os.path.join(backup_dir, 'uploads')
        if os.path.exists(Config.UPLOAD_FOLDER):
            shutil.copytree(Config.UPLOAD_FOLDER, files_dir)
        
        # Create zip archive
        zip_path = os.path.join(Config.BACKUP_DIR, f'backup_{backup_timestamp}.zip')
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, dirs, files in os.walk(backup_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    arcname = os.path.relpath(file_path, backup_dir)
                    zipf.write(file_path, arcname)
        
        # Cleanup temporary directory
        shutil.rmtree(backup_dir)
        
        # Update backup record
        backup.status = 'completed'
        backup.backup_path = zip_path
        backup.size = os.path.getsize(zip_path)
        backup.completed_at = datetime.utcnow()
        db.session.commit()
        
        # Log success
        print(f"Backup completed: {zip_path}")
        
    except Exception as e:
        backup = Backup.query.get(backup_id)
        if backup:
            backup.status = 'failed'
            db.session.commit()
        print(f"Backup failed: {e}")

# Start backup
@backup_bp.route('', methods=['POST'])
@jwt_required()
def start_backup():
    current_user_id = get_jwt_identity()
    data = request.get_json() or {}
    backup_type = data.get('type', 'full')
    storage_location = data.get('storage_location', 'local')
    description = data.get('description', '')

    backup = Backup(
        backup_type=backup_type,
        status='in_progress',
        created_at=datetime.utcnow()
    )
    db.session.add(backup)
    db.session.commit()

    # Start backup in thread (simplified - in production use Celery)
    import threading
    thread = threading.Thread(
        target=create_backup,
        args=(backup.id, backup_type, storage_location)
    )
    thread.daemon = True
    thread.start()

    audit = AuditLog(
        user_id=current_user_id,
        action='backup_start',
        resource_type='backup',
        resource_id=backup.id,
        details=f'Started {backup_type} backup: {description}'
    )
    db.session.add(audit)
    db.session.commit()

    return jsonify({
        'message': 'Backup started', 
        'backup_id': backup.id,
        'status': 'in_progress'
    }), 202

# Restore backup
@backup_bp.route('/<int:backup_id>/restore', methods=['POST'])
@jwt_required()
def restore_backup_route(backup_id):
    current_user_id = get_jwt_identity()
    current_user = db.session.get(User, current_user_id)
    
    if not current_user or current_user.role != 'admin':
        return jsonify({'error': 'Admin access required'}), 403
    
    backup = Backup.query.get(backup_id)
    if not backup:
        return jsonify({'error': 'Backup not found'}), 404
    if backup.status != 'completed':
        return jsonify({'error': 'Backup not completed'}), 400
    
    # In production, this would be a background task
    # For now, just mark as restoring
    backup.status = 'restoring'
    db.session.commit()

    audit = AuditLog(
        user_id=current_user_id,
        action='backup_restore',
        resource_type='backup',
        resource_id=backup_id,
        details='Started backup restoration'
    )
    db.session.add(audit)
    db.session.commit()

    return jsonify({
        'message': 'Restore process started',
        'warning': 'This will replace current data!'
    }), 202

# List backups (for frontend)
@backup_bp.route('', methods=['GET'])
@jwt_required()
def list_backups():
    backups = Backup.query.order_by(Backup.created_at.desc()).all()
    
    result = []
    for b in backups:
        # Calculate readable size
        size_readable = "N/A"
        if b.size:
            size_mb = b.size / (1024 * 1024)
            size_readable = f"{size_mb:.1f} MB" if size_mb < 1024 else f"{size_mb/1024:.1f} GB"
        
        result.append({
            'id': b.id,
            'backup_type': b.backup_type,
            'status': b.status,
            'created_at': b.created_at.strftime("%Y-%m-%d %I:%M %p") if b.created_at else 'N/A',
            'completed_at': b.completed_at.strftime("%Y-%m-%d %I:%M %p") if b.completed_at else 'N/A',
            'size': size_readable,
            'size_bytes': b.size
        })
    
    return jsonify(result), 200

# Get backup statistics
@backup_bp.route('/statistics', methods=['GET'])
@jwt_required()
def backup_statistics():
    current_user_id = get_jwt_identity()
    current_user = db.session.get(User, current_user_id)
    
    if not current_user or current_user.role != 'admin':
        return jsonify({'error': 'Admin access required'}), 403
    
    total_backups = Backup.query.count()
    completed_backups = Backup.query.filter_by(status='completed').count()
    failed_backups = Backup.query.filter_by(status='failed').count()
    
    # Calculate storage used
    backups = Backup.query.filter_by(status='completed').all()
    total_size = sum(b.size for b in backups if b.size)
    total_size_gb = total_size / (1024 * 1024 * 1024) if total_size else 0
    
    # Last successful backup
    last_backup = Backup.query.filter_by(status='completed')\
        .order_by(Backup.completed_at.desc()).first()
    
    return jsonify({
        'total': total_backups,
        'completed': completed_backups,
        'failed': failed_backups,
        'total_size_gb': round(total_size_gb, 2),
        'last_backup': last_backup.completed_at.strftime("%Y-%m-%d %H:%M") if last_backup else 'Never',
        'success_rate': round((completed_backups / total_backups * 100) if total_backups > 0 else 100, 1)
    }), 200