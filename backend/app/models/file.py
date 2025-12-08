# app/models/file.py
from app import db
from datetime import datetime

class CaseFile(db.Model):
    __tablename__ = 'case_files'
    
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(255), nullable=False)
    original_filename = db.Column(db.String(255), nullable=False)
    file_path = db.Column(db.String(500), nullable=False)
    file_size = db.Column(db.Integer)  # in bytes
    file_type = db.Column(db.String(50))
    document_type = db.Column(db.Enum('ruling', 'evidence', 'witness_statement', 'affidavit', 'pleading', 'exhibit', name='doc_types'))
    case_id = db.Column(db.Integer, db.ForeignKey('cases.id'), nullable=False)
    uploaded_by_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    ocr_text = db.Column(db.Text)  # Extracted text from OCR
    is_ocr_processed = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Backup relationship
    backups = db.relationship('FileBackup', backref='file', lazy=True)
    
    def to_dict(self):
        return {
            'id': self.id,
            'filename': self.filename,
            'original_filename': self.original_filename,
            'file_size': self.file_size,
            'file_type': self.file_type,
            'document_type': self.document_type,
            'case_id': self.case_id,
            'uploaded_by_id': self.uploaded_by_id,
            'is_ocr_processed': self.is_ocr_processed,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'ocr_text_preview': self.ocr_text[:200] + '...' if self.ocr_text and len(self.ocr_text) > 200 else self.ocr_text
        }
