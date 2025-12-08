# app/models/backup.py
from app import db
from datetime import datetime

class Backup(db.Model):
    __tablename__ = 'backups'
    
    id = db.Column(db.Integer, primary_key=True)
    backup_type = db.Column(db.Enum('full', 'incremental', 'differential', name='backup_types'))
    backup_path = db.Column(db.String(500))
    size = db.Column(db.BigInteger)  # in bytes
    status = db.Column(db.Enum('in_progress', 'completed', 'failed', name='backup_status'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    completed_at = db.Column(db.DateTime)
    
    def to_dict(self):
        return {
            'id': self.id,
            'backup_type': self.backup_type,
            'backup_path': self.backup_path,
            'size': self.size,
            'status': self.status,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None
        }

class FileBackup(db.Model):
    __tablename__ = 'file_backups'
    
    id = db.Column(db.Integer, primary_key=True)
    file_id = db.Column(db.Integer, db.ForeignKey('case_files.id'), nullable=False)
    backup_id = db.Column(db.Integer, db.ForeignKey('backups.id'), nullable=False)
    backup_file_path = db.Column(db.String(500), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
