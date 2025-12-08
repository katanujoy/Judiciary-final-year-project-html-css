from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.models import Backup, AuditLog, db
from app.utils.backup import create_backup, restore_backup
from datetime import datetime

backup_bp = Blueprint('backup', __name__)

# Start backup
@backup_bp.route('/backup', methods=['POST'])
@jwt_required()
def start_backup():
    current_user_id = get_jwt_identity()
    data = request.get_json()
    backup_type = data.get('type', 'full')
    storage_location = data.get('storage_location', 'local')

    backup = Backup(
        backup_type=backup_type,
        status='in_progress',
        created_at=datetime.utcnow()
    )
    db.session.add(backup)
    db.session.commit()

    create_backup.delay(backup.id, backup_type, storage_location)

    audit = AuditLog(
        user_id=current_user_id,
        action='backup_start',
        resource_type='backup',
        resource_id=backup.id,
        details=f'Started {backup_type} backup'
    )
    db.session.add(audit)
    db.session.commit()

    return jsonify({'message': 'Backup started', 'backup_id': backup.id}), 202

# Restore backup
@backup_bp.route('/backup/<int:backup_id>/restore', methods=['POST'])
@jwt_required()
def restore_backup_route(backup_id):
    current_user_id = get_jwt_identity()
    backup = Backup.query.get(backup_id)
    if not backup:
        return jsonify({'error': 'Backup not found'}), 404
    if backup.status != 'completed':
        return jsonify({'error': 'Backup not completed'}), 400

    restore_backup.delay(backup_id)

    audit = AuditLog(
        user_id=current_user_id,
        action='backup_restore',
        resource_type='backup',
        resource_id=backup_id,
        details='Started backup restoration'
    )
    db.session.add(audit)
    db.session.commit()

    return jsonify({'message': 'Restore process started'}), 202

# List backups (for frontend)
@backup_bp.route('/backup', methods=['GET'])
@jwt_required()
def list_backups():
    backups = Backup.query.order_by(Backup.created_at.desc()).all()
    return jsonify([{
        'id': b.id,
        'backup_type': b.backup_type,
        'status': b.status,
        'created_at': b.created_at.strftime("%Y-%m-%d %I:%M %p"),
        'size': b.size
    } for b in backups])
