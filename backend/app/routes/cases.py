# app/routes/cases.py
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from sqlalchemy import or_
from app.models import Case, User, AuditLog, db
from datetime import datetime

cases_bp = Blueprint("cases", __name__)

# ---------------------------------------------------------
# GET ALL CASES
# ---------------------------------------------------------
@cases_bp.route("/cases", methods=["GET"])
@jwt_required()
def get_cases():
    current_user_id = get_jwt_identity()
    current_user = User.query.get(current_user_id)

    if not current_user:
        return jsonify({"error": "Invalid user"}), 401

    # Base query
    query = Case.query

    # Judges ONLY see their assigned cases
    if current_user.role == "judge":
        query = query.filter_by(judge_id=current_user_id)

    # ----- Filters -----
    status = request.args.get("status")
    if status:
        query = query.filter_by(status=status)

    case_type = request.args.get("case_type")
    if case_type:
        query = query.filter_by(case_type=case_type)

    court_station = request.args.get("court_station")
    if court_station:
        query = query.filter_by(court_station=court_station)

    # Allow admin/clerk to filter by judge
    judge_id = request.args.get("judge_id")
    if judge_id and current_user.role in ["admin", "clerk"]:
        query = query.filter_by(judge_id=judge_id)

    # Search filter
    search = request.args.get("search")
    if search:
        search_pattern = f"%{search}%"
        query = query.filter(
            or_(
                Case.case_number.ilike(search_pattern),
                Case.title.ilike(search_pattern),
                Case.description.ilike(search_pattern)
            )
        )

    # Pagination
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 20, type=int)

    paginated = query.order_by(Case.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )

    # Get recent cases for dashboard (limit 5)
    recent = query.order_by(Case.created_at.desc()).limit(5).all()

    return jsonify({
        "cases": [case.to_dict() for case in paginated.items],
        "recent_cases": [case.to_dict() for case in recent],
        "total": paginated.total,
        "pages": paginated.pages,
        "current_page": page
    }), 200


# ---------------------------------------------------------
# CREATE CASE
# ---------------------------------------------------------
@cases_bp.route("/cases", methods=["POST"])
@jwt_required()
def create_case():
    current_user_id = get_jwt_identity()
    current_user = User.query.get(current_user_id)

    if not current_user:
        return jsonify({"error": "Invalid user"}), 401

    data = request.get_json() or {}

    # ----- Required fields -----
    if not data.get("case_number") or not data.get("title"):
        return jsonify({"error": "case_number and title are required"}), 400

    # Unique constraint
    if Case.query.filter_by(case_number=data["case_number"]).first():
        return jsonify({"error": "Case number already exists"}), 409

    # Assign judge:
    judge_id = data.get("judge_id")

    # Judge cannot assign cases to other judges
    if current_user.role == "judge":
        judge_id = current_user_id

    # Admin or Clerk — allow assignment
    if not judge_id:
        judge_id = current_user_id

    new_case = Case(
        case_number=data["case_number"],
        title=data["title"],
        description=data.get("description"),
        case_type=data.get("case_type"),
        judge_id=judge_id,
        court_station=data.get("court_station"),
        status=data.get("status", "active")
    )

    db.session.add(new_case)
    db.session.commit()

    # Audit Logging
    audit_entry = AuditLog(
        user_id=current_user_id,
        action="case_create",
        resource_type="case",
        resource_id=new_case.id,
        details=f"Created case {new_case.case_number}"
    )

    db.session.add(audit_entry)
    db.session.commit()

    return jsonify({
        "message": "Case created successfully",
        "case": new_case.to_dict()
    }), 201


# ---------------------------------------------------------
# GET SINGLE CASE
# ---------------------------------------------------------
@cases_bp.route("/cases/<int:case_id>", methods=["GET"])
@jwt_required()
def get_case(case_id):
    current_user_id = get_jwt_identity()
    current_user = User.query.get(current_user_id)

    if not current_user:
        return jsonify({"error": "Invalid user"}), 401

    case = Case.query.get_or_404(case_id)

    # Check permissions
    if current_user.role == "judge" and case.judge_id != current_user_id:
        return jsonify({"error": "Access denied"}), 403

    # Include files in response
    case_data = case.to_dict()
    case_data["files"] = [file.to_dict() for file in case.files]

    return jsonify({"case": case_data}), 200


# ---------------------------------------------------------
# UPDATE CASE
# ---------------------------------------------------------
@cases_bp.route("/cases/<int:case_id>", methods=["PUT"])
@jwt_required()
def update_case(case_id):
    current_user_id = get_jwt_identity()
    current_user = User.query.get(current_user_id)

    if not current_user:
        return jsonify({"error": "Invalid user"}), 401

    case = Case.query.get_or_404(case_id)

    # Check permissions
    if current_user.role == "judge" and case.judge_id != current_user_id:
        return jsonify({"error": "Access denied"}), 403

    data = request.get_json() or {}

    # Update fields
    if "title" in data:
        case.title = data["title"]
    if "description" in data:
        case.description = data["description"]
    if "status" in data:
        case.status = data["status"]
    if "case_type" in data:
        case.case_type = data["case_type"]
    if "court_station" in data:
        case.court_station = data["court_station"]

    # Only admin/clerk can change judge
    if "judge_id" in data and current_user.role in ["admin", "clerk"]:
        judge = User.query.get(data["judge_id"])
        if judge and judge.role == "judge":
            case.judge_id = data["judge_id"]

    case.updated_at = datetime.utcnow()
    db.session.commit()

    # Audit Logging
    audit_entry = AuditLog(
        user_id=current_user_id,
        action="case_update",
        resource_type="case",
        resource_id=case_id,
        details=f"Updated case {case.case_number}"
    )

    db.session.add(audit_entry)
    db.session.commit()

    return jsonify({
        "message": "Case updated successfully",
        "case": case.to_dict()
    }), 200


# ---------------------------------------------------------
# DELETE CASE
# ---------------------------------------------------------
@cases_bp.route("/cases/<int:case_id>", methods=["DELETE"])
@jwt_required()
def delete_case(case_id):
    current_user_id = get_jwt_identity()
    current_user = User.query.get(current_user_id)

    if not current_user or current_user.role != "admin":
        return jsonify({"error": "Admin access required"}), 403

    case = Case.query.get_or_404(case_id)

    # Audit before deletion
    audit_entry = AuditLog(
        user_id=current_user_id,
        action="case_delete",
        resource_type="case",
        resource_id=case_id,
        details=f"Deleted case {case.case_number}"
    )

    db.session.add(audit_entry)
    db.session.delete(case)
    db.session.commit()

    return jsonify({"message": "Case deleted successfully"}), 200


# ---------------------------------------------------------
# GET CASE STATISTICS
# ---------------------------------------------------------
@cases_bp.route("/cases/statistics", methods=["GET"])
@jwt_required()
def get_case_statistics():
    current_user_id = get_jwt_identity()
    current_user = User.query.get(current_user_id)

    if not current_user:
        return jsonify({"error": "Invalid user"}), 401

    # Base query
    query = Case.query

    if current_user.role == "judge":
        query = query.filter_by(judge_id=current_user_id)

    total_cases = query.count()
    active_cases = query.filter_by(status="active").count()
    pending_cases = query.filter_by(status="pending").count()
    closed_cases = query.filter_by(status="closed").count()

    # Cases by type
    criminal_cases = query.filter_by(case_type="criminal").count()
    civil_cases = query.filter_by(case_type="civil").count()
    commercial_cases = query.filter_by(case_type="commercial").count()
    constitutional_cases = query.filter_by(case_type="constitutional").count()

    # Recent activity (last 7 days)
    from datetime import datetime, timedelta
    week_ago = datetime.utcnow() - timedelta(days=7)
    recent_cases = query.filter(Case.created_at >= week_ago).count()

    return jsonify({
        "total": total_cases,
        "active": active_cases,
        "pending": pending_cases,
        "closed": closed_cases,
        "by_type": {
            "criminal": criminal_cases,
            "civil": civil_cases,
            "commercial": commercial_cases,
            "constitutional": constitutional_cases
        },
        "recent_week": recent_cases
    }), 200