# app/models/user.py
from app import db
from datetime import datetime

class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    full_name = db.Column(db.String(100), nullable=False)
    employee_id = db.Column(db.String(20), unique=True, nullable=False)
    role = db.Column(
        db.Enum("judge", "clerk", "admin", name="user_roles"),
        nullable=False
    )
    court_station = db.Column(db.String(100))
    is_active = db.Column(db.Boolean, default=True)
    is_approved = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime)

    # Relationships
    cases = db.relationship("Case", backref="judge", lazy=True)
    uploaded_files = db.relationship("CaseFile", backref="uploaded_by", lazy=True)
    audit_logs = db.relationship("AuditLog", backref="user", lazy=True)

    def to_dict(self):
        return {
            "id": self.id,
            "email": self.email,
            "full_name": self.full_name,
            "employee_id": self.employee_id,
            "role": self.role,
            "court_station": self.court_station,
            "is_active": self.is_active,
            "is_approved": self.is_approved,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "last_login": self.last_login.isoformat() if self.last_login else None,
        }
