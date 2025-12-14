from app import create_app, db
from app.models import User, Case, CaseReview, Notification
from app.utils.auth import hash_password
from flask_cors import CORS

app = create_app()
CORS(app, resources={r"/*": {"origins": "*"}}, supports_credentials=True)

def seed_users():
    """Seed admin, judges, and clerks."""
    users = [
        # Admin
        {
            "email": "admin@judiciary.go.ke",
            "password": "Admin123",
            "full_name": "System Administrator",
            "employee_id": "ADM-001",
            "role": "admin",
            "court_station": "Nairobi High Court",
        },
        # Judges
        {
            "email": "judge.mwangi@judiciary.go.ke",
            "password": "Judge123",
            "full_name": "Hon. Justice Mwangi",
            "employee_id": "JDG-101",
            "role": "judge",
            "court_station": "Milimani Law Courts",
        },
        {
            "email": "judge.kimani@judiciary.go.ke",
            "password": "Judge456",
            "full_name": "Hon. Justice Kimani",
            "employee_id": "JDG-102",
            "role": "judge",
            "court_station": "Kisumu High Court",
        },
        # Clerks
        {
            "email": "clerk.wanjiru@judiciary.go.ke",
            "password": "Clerk123",
            "full_name": "Clerk Wanjiru",
            "employee_id": "CLK-201",
            "role": "clerk",
            "court_station": "Nakuru Law Courts",
        },
        {
            "email": "clerk.omondi@judiciary.go.ke",
            "password": "Clerk456",
            "full_name": "Clerk Omondi",
            "employee_id": "CLK-202",
            "role": "clerk",
            "court_station": "Mombasa Law Courts",
        }
    ]

    for u in users:
        if not User.query.filter_by(email=u["email"]).first():
            user = User(
                email=u["email"],
                password_hash=hash_password(u["password"]),
                full_name=u["full_name"],
                employee_id=u["employee_id"],
                role=u["role"],
                court_station=u["court_station"],
                is_approved=True,
                is_active=True
            )
            db.session.add(user)

    db.session.commit()
    print("👤 Users seeded successfully.")


def seed_cases():
    """Seed sample cases."""
    cases_data = [
        {
            "case_number": "CRIM-2025-001",
            "title": "Republic vs John Doe",
            "case_type": "Criminal",
            "status": "Pending",
            "description": "Suspected theft and assault."
        },
        {
            "case_number": "CIVIL-2025-004",
            "title": "Jane Doe vs TechCorp Ltd.",
            "case_type": "Civil",
            "status": "Ongoing",
            "description": "Employment termination dispute."
        },
        {
            "case_number": "FAMILY-2025-010",
            "title": "Mwangi Family Dispute",
            "case_type": "Family",
            "status": "Closed",
            "description": "Child custody case."
        }
    ]

    for c in cases_data:
        if not Case.query.filter_by(case_number=c["case_number"]).first():
            case = Case(**c)
            db.session.add(case)

    db.session.commit()
    print("📄 Cases seeded successfully.")


def seed_reviews():
    """Seed case reviews."""
    judge = User.query.filter_by(role="judge").first()
    case = Case.query.first()

    if judge and case:
        review = CaseReview(
            judge_id=judge.id,
            case_id=case.id,
            content="Initial review completed. Awaiting more evidence."
        )
        db.session.add(review)
        db.session.commit()
        print("📝 Case reviews seeded successfully.")
    else:
        print("⚠ Skipped reviews seeding — missing judge/case.")


def seed_notifications():
    """Seed notifications."""
    user = User.query.filter_by(role="clerk").first()

    if user:
        notification = Notification(
            user_id=user.id,
            title="New Case Assigned",
            message="You have been assigned CRIM-2025-001 for documentation.",
            is_read=False
        )
        db.session.add(notification)
        db.session.commit()
        print("🔔 Notifications seeded successfully.")
    else:
        print("⚠ Skipped notifications seeding — no clerk found.")


def run_seeds():
    with app.app_context():
        print("🔄 Creating database tables...")
        db.create_all()

        print("🌱 Seeding database...")
        seed_users()
        seed_cases()
        seed_reviews()
        seed_notifications()

        print("\n🎉 SEEDING COMPLETE!\n")


if __name__ == "__main__":
    run_seeds()
