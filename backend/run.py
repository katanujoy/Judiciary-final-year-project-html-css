from app import create_app, db
from app.models import User
from app.utils.auth import hash_password

app = create_app()

def create_tables_and_admin():
    """Create tables and initial admin user if not exists"""
    with app.app_context():
        db.create_all()
        
        if not User.query.filter_by(role='admin').first():
            admin_user = User(
                email='admin@judiciary.go.ke',
                password_hash=hash_password('Admin123'),
                full_name='System Administrator',
                employee_id='ADM-001',
                role='admin',
                court_station='Nairobi High Court',
                is_approved=True,
                is_active=True
            )
            db.session.add(admin_user)
            db.session.commit()
            print("✅ Initial admin user created: admin@judiciary.go.ke / Admin123")
        else:
            print("✅ Admin user already exists")

if __name__ == '__main__':
    create_tables_and_admin()  # run initialization here
    app.run(debug=True, host='0.0.0.0', port=5000)
