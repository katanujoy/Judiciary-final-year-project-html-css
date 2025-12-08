# app/utils/backup.py
import os
import shutil
from datetime import datetime
from app import db, create_app
from app.models.backup import Backup, FileBackup
from app.models.file import CaseFile
from .celery import celery

@celery.task
def create_backup(backup_id, backup_type, storage_location=None):
    """
    Background task to create a system backup.
    `storage_location` can be used for cloud storage (optional).
    """
    with create_app().app_context():
        backup = Backup.query.get(backup_id)
        if not backup:
            raise ValueError(f"No backup found with id {backup_id}")
        
        try:
            # Create backup directory
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_dir = os.path.join('backups', f"backup_{backup_id}_{timestamp}")
            os.makedirs(backup_dir, exist_ok=True)

            total_size = 0
            files = CaseFile.query.all()

            for file in files:
                if os.path.exists(file.file_path):
                    backup_file_path = os.path.join(backup_dir, f"file_{file.id}_{file.filename}")
                    # Copy file to backup directory
                    shutil.copy2(file.file_path, backup_file_path)

                    # Record in FileBackup table
                    file_backup = FileBackup(
                        file_id=file.id,
                        backup_id=backup_id,
                        backup_file_path=backup_file_path
                    )
                    db.session.add(file_backup)
                    total_size += file.file_size or 0

            backup.size = total_size
            backup.status = 'completed'
            backup.completed_at = datetime.utcnow()
            db.session.commit()
        
        except Exception as e:
            backup.status = 'failed'
            db.session.commit()
            raise e


def restore_backup(backup_id):
    """
    Placeholder for restoring a backup.
    Replace with actual implementation when ready.
    """
    print(f"Restoring backup {backup_id} (not implemented yet).")
    return False
