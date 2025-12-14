# app/routes/search.py
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.models import CaseFile, Case, User
from sqlalchemy import or_, and_
from datetime import datetime, timedelta

search_bp = Blueprint('search', __name__)

@search_bp.route('', methods=['GET'])
@jwt_required()
def search_files():
    current_user_id = get_jwt_identity()
    current_user = User.query.get(current_user_id)
    
    if not current_user:
        return jsonify({'error': 'Invalid user'}), 401
    
    query = request.args.get('q', '').strip()
    case_number = request.args.get('case_number', '').strip()
    document_type = request.args.get('document_type')
    judge_id = request.args.get('judge_id')
    date_from = request.args.get('date_from')
    date_to = request.args.get('date_to')
    search_in_content = request.args.get('search_in_content', 'true').lower() == 'true'
    
    if not query and not case_number:
        return jsonify({'error': 'Search query or case number required'}), 400
    
    # Build search query
    search_query = CaseFile.query.join(Case)
    
    # Apply user permissions
    if current_user.role == 'judge':
        search_query = search_query.filter(Case.judge_id == current_user_id)
    
    # Search conditions
    conditions = []
    
    if query:
        # Search in filename
        filename_condition = CaseFile.original_filename.ilike(f'%{query}%')
        
        # Search in OCR text if enabled
        content_condition = None
        if search_in_content:
            content_condition = CaseFile.ocr_text.ilike(f'%{query}%')
        
        # Search in case details
        case_conditions = or_(
            Case.case_number.ilike(f'%{query}%'),
            Case.title.ilike(f'%{query}%'),
            Case.description.ilike(f'%{query}%')
        )
        
        # Combine conditions
        if content_condition:
            search_condition = or_(filename_condition, content_condition, case_conditions)
        else:
            search_condition = or_(filename_condition, case_conditions)
        
        conditions.append(search_condition)
    
    if case_number:
        conditions.append(Case.case_number.ilike(f'%{case_number}%'))
    
    if document_type:
        conditions.append(CaseFile.document_type == document_type)
    
    # Apply judge filter (only for admin/clerk)
    if judge_id and current_user.role in ['admin', 'clerk']:
        conditions.append(Case.judge_id == judge_id)
    
    # Apply date filters
    if date_from:
        try:
            from_date = datetime.strptime(date_from, '%Y-%m-%d')
            conditions.append(CaseFile.created_at >= from_date)
        except ValueError:
            pass
    
    if date_to:
        try:
            to_date = datetime.strptime(date_to, '%Y-%m-%d')
            # Add one day to include the entire day
            to_date = to_date + timedelta(days=1)
            conditions.append(CaseFile.created_at <= to_date)
        except ValueError:
            pass
    
    # Apply all conditions
    if conditions:
        search_query = search_query.filter(and_(*conditions))
    
    # Pagination
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    
    # Execute query with pagination
    results = search_query.order_by(CaseFile.created_at.desc())\
        .paginate(page=page, per_page=per_page, error_out=False)
    
    # Format results with relevance scoring
    formatted_results = []
    for result in results.items:
        result_dict = result.to_dict()
        
        # Calculate relevance score (simplified)
        relevance = 0
        if query:
            query_lower = query.lower()
            if query_lower in result.original_filename.lower():
                relevance += 30
            if result.ocr_text and query_lower in result.ocr_text.lower():
                relevance += 50
            if query_lower in result.case.case_number.lower():
                relevance += 20
        
        result_dict['relevance'] = min(relevance, 100)
        result_dict['case'] = result.case.to_dict() if result.case else None
        
        formatted_results.append(result_dict)
    
    # Sort by relevance if there's a query
    if query:
        formatted_results.sort(key=lambda x: x['relevance'], reverse=True)
    
    return jsonify({
        'results': formatted_results,
        'total': results.total,
        'pages': results.pages,
        'current_page': page,
        'per_page': per_page
    })

@search_bp.route('/advanced', methods=['GET'])
@jwt_required()
def advanced_search():
    """Advanced search with more options"""
    current_user_id = get_jwt_identity()
    current_user = User.query.get(current_user_id)
    
    if not current_user:
        return jsonify({'error': 'Invalid user'}), 401
    
    # Get search parameters
    query = request.args.get('query', '').strip()
    exact_phrase = request.args.get('exact_phrase', 'false').lower() == 'true'
    include_ocr = request.args.get('include_ocr', 'true').lower() == 'true'
    include_metadata = request.args.get('include_metadata', 'true').lower() == 'true'
    
    if not query:
        return jsonify({'error': 'Search query required'}), 400
    
    # Build search query
    search_query = CaseFile.query.join(Case)
    
    # Apply user permissions
    if current_user.role == 'judge':
        search_query = search_query.filter(Case.judge_id == current_user_id)
    
    # Build search conditions
    conditions = []
    
    if exact_phrase:
        # Exact phrase matching
        if include_metadata:
            conditions.append(CaseFile.original_filename.contains(query))
        if include_ocr and query:
            conditions.append(CaseFile.ocr_text.contains(query))
        conditions.append(Case.case_number.contains(query))
        conditions.append(Case.title.contains(query))
    else:
        # Fuzzy matching
        search_terms = query.split()
        for term in search_terms:
            term_conditions = []
            if include_metadata:
                term_conditions.append(CaseFile.original_filename.ilike(f'%{term}%'))
            if include_ocr:
                term_conditions.append(CaseFile.ocr_text.ilike(f'%{term}%'))
            term_conditions.append(Case.case_number.ilike(f'%{term}%'))
            term_conditions.append(Case.title.ilike(f'%{term}%'))
            
            if term_conditions:
                conditions.append(or_(*term_conditions))
    
    # Apply conditions
    if conditions:
        search_query = search_query.filter(or_(*conditions))
    
    # Execute query
    files = search_query.order_by(CaseFile.created_at.desc()).limit(100).all()
    
    # Format results
    formatted_results = []
    for file in files:
        result = file.to_dict()
        result['case'] = file.case.to_dict() if file.case else None
        formatted_results.append(result)
    
    return jsonify({
        'results': formatted_results,
        'count': len(formatted_results)
    })