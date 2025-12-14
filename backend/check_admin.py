# check_admin.py
from app import create_app, db
from app.models import User
from app.utils.auth import hash_password

app = create_app()

with app.app_context():
    print("Checking database...")
    
    # Check if admin exists
    admin = User.query.filter_by(email='admin@judiciary.go.ke').first()
    
    if admin:
        print(f"✅ Admin user found:")
        print(f"   Email: {admin.email}")
        print(f"   Role: {admin.role}")
        print(f"   Approved: {admin.is_approved}")
        print(f"   Active: {admin.is_active}")
        
        # Test password
        from app.utils.auth import verify_password
        test_password = "Admin123"
        is_correct = verify_password(test_password, admin.password_hash)
        print(f"   Password 'Admin123' correct: {is_correct}")
        
        if not is_correct:
            print(f"\n⚠️  Password doesn't match. Resetting password...")
            admin.password_hash = hash_password("Admin123")
            db.session.commit()
            print(f"✅ Password reset to 'Admin123'")
    else:
        print("❌ Admin user not found!")
        print("\nCreating admin user...")
        
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
        print("✅ Admin user created:")
        print(f"   Email: admin@judiciary.go.ke")
        print(f"   Password: Admin123")
        print(f"   Role: Administrator")
    
    # Count all users
    user_count = User.query.count()
    print(f"\nTotal users in database: {user_count}")