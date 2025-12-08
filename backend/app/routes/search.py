# app/routes/search.py
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from app.models import CaseFile, Case
from sqlalchemy import or_

search_bp = Blueprint('search', __name__)

@search_bp.route('/search', methods=['GET'])
@jwt_required()
def search_files():
    query = request.args.get('q', '')
    case_number = request.args.get('case_number')
    document_type = request.args.get('document_type')
    date_from = request.args.get('date_from')
    date_to = request.args.get('date_to')
    
    if not query and not case_number:
        return jsonify({'error': 'Search query or case number required'}), 400
    
    # Build search query
    search_query = CaseFile.query.join(Case)
    
    if query:
        search_query = search_query.filter(
            or_(
                CaseFile.original_filename.ilike(f'%{query}%'),
                CaseFile.ocr_text.ilike(f'%{query}%'),
                Case.case_number.ilike(f'%{query}%'),
                Case.title.ilike(f'%{query}%')
            )
        )
    
    if case_number:
        search_query = search_query.filter(Case.case_number.ilike(f'%{case_number}%'))
    
    if document_type:
        search_query = search_query.filter(CaseFile.document_type == document_type)
    
    # Apply date filters
    if date_from:
        search_query = search_query.filter(CaseFile.created_at >= date_from)
    if date_to:
        search_query = search_query.filter(CaseFile.created_at <= date_to)
    
    # Pagination
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    results = search_query.paginate(page=page, per_page=per_page, error_out=False)
    
    return jsonify({
        'results': [result.to_dict() for result in results.items],
        'total': results.total,
        'pages': results.pages,
        'current_page': page
    })