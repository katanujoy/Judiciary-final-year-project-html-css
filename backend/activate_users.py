# activate_users.py
from app import create_app, db
from app.models import User

app = create_app()

with app.app_context():
    # Get all users
    users = User.query.all()
    
    print(f"Found {len(users)} users in database:")
    
    # Activate all users
    activated_count = 0
    for user in users:
        print(f"  - {user.email} (ID: {user.id}): is_active={user.is_active}, is_approved={user.is_approved}")
        
        if not user.is_active or not user.is_approved:
            user.is_active = True
            user.is_approved = True
            activated_count += 1
            print(f"    -> Activated!")
    
    if activated_count > 0:
        db.session.commit()
        print(f"\n✅ Activated {activated_count} users!")
    else:
        print("\n✅ All users are already active!")
    
    # Show updated status
    print("\nUpdated user status:")
    for user in User.query.all():
        print(f"  - {user.email}: active={user.is_active}, approved={user.is_approved}")