# app/routes/cases.py
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.models import Case, User, db, AuditLog
from sqlalchemy import or_

cases_bp = Blueprint('cases', __name__)

@cases_bp.route('/cases', methods=['GET'])
@jwt_required()
def get_cases():
    current_user_id = get_jwt_identity()
    current_user = User.query.get(current_user_id)
    
    # Build query based on user role
    if current_user.role == 'judge':
        query = Case.query.filter_by(judge_id=current_user_id)
    else:
        query = Case.query
    
    # Apply filters
    status = request.args.get('status')
    if status:
        query = query.filter_by(status=status)
    
    judge_id = request.args.get('judge_id')
    if judge_id and current_user.role in ['admin', 'clerk']:
        query = query.filter_by(judge_id=judge_id)
    
    search = request.args.get('search')
    if search:
        query = query.filter(
            or_(
                Case.case_number.ilike(f'%{search}%'),
                Case.title.ilike(f'%{search}%'),
                Case.description.ilike(f'%{search}%')
            )
        )
    
    # Pagination
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    cases = query.paginate(page=page, per_page=per_page, error_out=False)
    
    return jsonify({
        'cases': [case.to_dict() for case in cases.items],
        'total': cases.total,
        'pages': cases.pages,
        'current_page': page
    })

@cases_bp.route('/cases', methods=['POST'])
@jwt_required()
def create_case():
    current_user_id = get_jwt_identity()
    data = request.get_json()
    
    # Validate required fields
    if not all(k in data for k in ['case_number', 'title']):
        return jsonify({'error': 'Case number and title are required'}), 400
    
    # Check if case number exists
    if Case.query.filter_by(case_number=data['case_number']).first():
        return jsonify({'error': 'Case number already exists'}), 409
    
    case = Case(
        case_number=data['case_number'],
        title=data['title'],
        description=data.get('description'),
        case_type=data.get('case_type'),
        judge_id=data.get('judge_id', current_user_id),
        court_station=data.get('court_station')
    )
    
    db.session.add(case)
    db.session.commit()
    
    # Audit log
    audit_log = AuditLog(
        user_id=current_user_id,
        action='case_create',
        resource_type='case',
        resource_id=case.id,
        details=f'Created case {case.case_number}'
    )
    db.session.add(audit_log)
    db.session.commit()
    
    return jsonify({'message': 'Case created successfully', 'case': case.to_dict()}), 201