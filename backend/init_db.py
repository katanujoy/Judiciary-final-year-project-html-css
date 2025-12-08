import os
import sys
from datetime import datetime

# Add app directory to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

# Use DevelopmentConfig explicitly
from config import DevelopmentConfig
from app import create_app, db

# Import models
from app.models.user import User
from app.models.case import Case
from app.models.file import CaseFile
from app.models.backup import Backup, FileBackup
from app.models.audit import AuditLog

# Import utilities
from app.utils.auth import hash_password

def init_database():
    """Initialize the database with default users, cases, and backups."""
    app = create_app(config_class=DevelopmentConfig)

    with app.app_context():
        try:
            # --- Create all tables ---
            print("Creating database tables...")
            db.create_all()
            print("✅ Tables created successfully!")

            # --- Create default admin user ---
            admin_user = User.query.filter_by(email='admin@judiciary.go.ke').first()
            if not admin_user:
                admin_user = User(
                    email='admin@judiciary.go.ke',
                    password_hash=hash_password('Admin123'),
                    full_name='System Administrator',
                    employee_id='ADMIN-001',
                    role='admin',
                    court_station='Nairobi High Court',
                    is_approved=True,
                    is_active=True,
                    created_at=datetime.utcnow()
                )
                db.session.add(admin_user)
                db.session.commit()
                print("✅ Default admin user created: admin@judiciary.go.ke / Admin123")
            else:
                print("✅ Admin user already exists")

            # --- Create sample judge ---
            judge_user = User.query.filter_by(email='judge.katanu@judiciary.go.ke').first()
            if not judge_user:
                judge_user = User(
                    email='judge.katanu@judiciary.go.ke',
                    password_hash=hash_password('Judge123'),
                    full_name='Justice Joy Katanu',
                    employee_id='J-001',
                    role='judge',
                    court_station='Nairobi High Court',
                    is_approved=True,
                    is_active=True,
                    created_at=datetime.utcnow()
                )
                db.session.add(judge_user)

            # --- Create sample clerk ---
            clerk_user = User.query.filter_by(email='clerk.mwangi@judiciary.go.ke').first()
            if not clerk_user:
                clerk_user = User(
                    email='clerk.mwangi@judiciary.go.ke',
                    password_hash=hash_password('Clerk123'),
                    full_name='Clerk John Mwangi',
                    employee_id='CLERK-001',
                    role='clerk',
                    court_station='Nairobi High Court',
                    is_approved=True,
                    is_active=True,
                    created_at=datetime.utcnow()
                )
                db.session.add(clerk_user)

            db.session.commit()

            # --- Create sample cases ---
            if Case.query.count() == 0:
                sample_cases = [
                    Case(
                        case_number='CR-2024-001',
                        title='State vs. John Doe - Criminal Case',
                        description='Criminal case involving theft and fraud charges',
                        case_type='Criminal',
                        judge_id=judge_user.id,
                        court_station='Nairobi High Court',
                        status='active',
                        created_at=datetime.utcnow(),
                        updated_at=datetime.utcnow()
                    ),
                    Case(
                        case_number='CV-2024-045',
                        title='Land Dispute - Nakuru County',
                        description='Civil land dispute between family members',
                        case_type='Civil',
                        judge_id=judge_user.id,
                        court_station='Nairobi High Court',
                        status='pending',
                        created_at=datetime.utcnow(),
                        updated_at=datetime.utcnow()
                    ),
                    Case(
                        case_number='MC-2024-123',
                        title='Commercial Arbitration - ABC Corp',
                        description='Commercial arbitration between ABC Corp and XYZ Ltd',
                        case_type='Commercial',
                        judge_id=judge_user.id,
                        court_station='Nairobi High Court',
                        status='active',
                        created_at=datetime.utcnow(),
                        updated_at=datetime.utcnow()
                    )
                ]
                db.session.add_all(sample_cases)
                db.session.commit()
                print("✅ Sample cases created!")
            else:
                print("✅ Cases already exist in database")

            # --- Create sample backup records ---
            if Backup.query.count() == 0:
                sample_backups = [
                    Backup(
                        backup_type='full',
                        status='completed',
                        backup_path='local/backups/full_backup.zip',
                        size=18_200_000_000,
                        created_at=datetime.utcnow(),
                        completed_at=datetime.utcnow()
                    ),
                    Backup(
                        backup_type='incremental',
                        status='completed',
                        backup_path='local/backups/incremental_backup.zip',
                        size=1_500_000_000,
                        created_at=datetime.utcnow(),
                        completed_at=datetime.utcnow()
                    )
                ]
                db.session.add_all(sample_backups)
                db.session.commit()
                print("✅ Sample backup records created!")
            else:
                print("✅ Backup records already exist")

            print("\n🎉 === Database Initialization Complete ===")
            print("Default users created:")
            print("1. Admin    - admin@judiciary.go.ke / Admin123")
            print("2. Judge    - judge.katanu@judiciary.go.ke / Judge123")
            print("3. Clerk    - clerk.mwangi@judiciary.go.ke / Clerk123")

        except Exception as e:
            print(f"❌ Error during database initialization: {str(e)}")
            db.session.rollback()

if __name__ == '__main__':
    init_database()
