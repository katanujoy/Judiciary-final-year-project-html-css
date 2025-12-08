# app/models/case.py
from app import db
from datetime import datetime

class Case(db.Model):
    __tablename__ = 'cases'
    
    id = db.Column(db.Integer, primary_key=True)
    case_number = db.Column(db.String(50), unique=True, nullable=False)
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)
    case_type = db.Column(db.Enum('criminal', 'civil', 'commercial', 'constitutional', name='case_types'))
    status = db.Column(db.Enum('active', 'pending', 'closed', 'archived', name='case_status'), default='active')
    judge_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    court_station = db.Column(db.String(100))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    files = db.relationship('CaseFile', backref='case', lazy=True, cascade='all, delete-orphan')
    
    def to_dict(self):
        return {
            'id': self.id,
            'case_number': self.case_number,
            'title': self.title,
            'description': self.description,
            'case_type': self.case_type,
            'status': self.status,
            'judge_id': self.judge_id,
            'court_station': self.court_station,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'file_count': len(self.files)
        }
