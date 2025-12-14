# create_tables.py
from app import create_app, db
from app.models import User, Case, CaseFile, Backup, AuditLog
from app.utils.auth import hash_password
import os

print("🔧 Creating Judiciary System Database...")
print("="*60)

app = create_app()

with app.app_context():
    # Create all tables
    print("Creating database tables...")
    db.create_all()
    
    # Create upload and backup directories
    print("Creating directories...")
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    os.makedirs(app.config['BACKUP_DIR'], exist_ok=True)
    print(f"✓ Upload directory: {app.config['UPLOAD_FOLDER']}")
    print(f"✓ Backup directory: {app.config['BACKUP_DIR']}")
    
    # Create admin user if not exists
    print("\nChecking admin user...")
    admin = User.query.filter_by(email='admin@judiciary.go.ke').first()
    
    if not admin:
        print("Creating admin user...")
        admin = User(
            email='admin@judiciary.go.ke',
            password_hash=hash_password('Admin123'),
            full_name='System Administrator',
            employee_id='ADMIN-001',
            role='admin',
            court_station='Nairobi High Court',
            is_active=True,
            is_approved=True
        )
        db.session.add(admin)
        db.session.commit()
        print("✓ Admin user created successfully!")
        print(f"  Email: admin@judiciary.go.ke")
        print(f"  Password: Admin123")
        print(f"  Role: Administrator")
    else:
        print("✓ Admin user already exists")
        print(f"  Email: {admin.email}")
        print(f"  Role: {admin.role}")
        print(f"  Approved: {admin.is_approved}")
    
    # Create some test users
    print("\nCreating test users...")
    
    # Test judge
    judge = User.query.filter_by(email='judge.katanu@judiciary.go.ke').first()
    if not judge:
        judge = User(
            email='judge.katanu@judiciary.go.ke',
            password_hash=hash_password('Judge123'),
            full_name='Justice Joy Katanu',
            employee_id='J-001',
            role='judge',
            court_station='Nairobi High Court',
            is_active=True,
            is_approved=True
        )
        db.session.add(judge)
        print("✓ Created test judge")
    
    # Test clerk
    clerk = User.query.filter_by(email='clerk.wanjiru@judiciary.go.ke').first()
    if not clerk:
        clerk = User(
            email='clerk.wanjiru@judiciary.go.ke',
            password_hash=hash_password('Clerk123'),
            full_name='Clerk Mary Wanjiru',
            employee_id='C1-001',
            role='clerk',
            court_station='Nairobi High Court',
            is_active=True,
            is_approved=True
        )
        db.session.add(clerk)
        print("✓ Created test clerk")
    
    db.session.commit()
    
    # Create some test cases
    print("\nCreating test cases...")
    
    test_cases = [
        {
            'case_number': 'CR-2024-001',
            'title': 'State vs. John Doe - Criminal Fraud',
            'description': 'Criminal case involving allegations of financial fraud',
            'case_type': 'criminal',
            'status': 'active',
            'court_station': 'Nairobi High Court'
        },
        {
            'case_number': 'CV-2024-045',
            'title': 'Land Dispute - Nakuru County',
            'description': 'Civil land dispute between two families',
            'case_type': 'civil',
            'status': 'pending',
            'court_station': 'Nakuru High Court'
        },
        {
            'case_number': 'MC-2024-123',
            'title': 'Commercial Arbitration - ABC Corp',
            'description': 'Commercial arbitration between two corporations',
            'case_type': 'commercial',
            'status': 'active',
            'court_station': 'Mombasa Law Courts'
        }
    ]
    
    case_count = 0
    for case_data in test_cases:
        existing = Case.query.filter_by(case_number=case_data['case_number']).first()
        if not existing:
            case = Case(
                case_number=case_data['case_number'],
                title=case_data['title'],
                description=case_data['description'],
                case_type=case_data['case_type'],
                status=case_data['status'],
                judge_id=admin.id if admin else 1,
                court_station=case_data['court_station']
            )
            db.session.add(case)
            case_count += 1
    
    if case_count > 0:
        db.session.commit()
        print(f"✓ Created {case_count} test cases")
    else:
        print("✓ Test cases already exist")
    
    # Count all records
    print("\n" + "="*60)
    print("📊 Database Summary:")
    print(f"  Users: {User.query.count()}")
    print(f"  Cases: {Case.query.count()}")
    print(f"  Files: {CaseFile.query.count()}")
    print(f"  Backups: {Backup.query.count()}")
    print(f"  Audit Logs: {AuditLog.query.count()}")
    print("="*60)
    print("\n✅ Database setup completed successfully!")
    print("\nYou can now run the backend with: python run.py")
    print("Login credentials:")
    print("  Admin: admin@judiciary.go.ke / Admin123")
    print("  Judge: judge.katanu@judiciary.go.ke / Judge123")
    print("  Clerk: clerk.wanjiru@judiciary.go.ke / Clerk123")