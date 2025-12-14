# app/routes/reports.py
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.models import Case, User, CaseFile, AuditLog, db
from datetime import datetime, timedelta
import json

reports_bp = Blueprint('reports', __name__)

@reports_bp.route('/dashboard', methods=['GET'])
@jwt_required()
def dashboard_report():
    """Get dashboard statistics"""
    current_user_id = get_jwt_identity()
    current_user = User.query.get(current_user_id)
    
    if not current_user:
        return jsonify({'error': 'Invalid user'}), 401
    
    # Base queries
    cases_query = Case.query
    files_query = CaseFile.query
    
    # Filter by user role
    if current_user.role == 'judge':
        cases_query = cases_query.filter_by(judge_id=current_user_id)
        files_query = files_query.join(Case).filter(Case.judge_id == current_user_id)
    
    # Calculate statistics
    total_cases = cases_query.count()
    active_cases = cases_query.filter_by(status='active').count()
    pending_cases = cases_query.filter_by(status='pending').count()
    closed_cases = cases_query.filter_by(status='closed').count()
    
    total_files = files_query.count()
    
    # Recent activity (last 7 days)
    week_ago = datetime.utcnow() - timedelta(days=7)
    recent_files = files_query.filter(CaseFile.created_at >= week_ago).count()
    recent_cases = cases_query.filter(Case.created_at >= week_ago).count()
    
    # Cases by type
    cases_by_type = {}
    for case_type in ['criminal', 'civil', 'commercial', 'constitutional']:
        count = cases_query.filter_by(case_type=case_type).count()
        if count > 0:
            cases_by_type[case_type] = count
    
    # Files by document type
    files_by_type = {}
    for doc_type in ['ruling', 'evidence', 'witness_statement', 'affidavit', 'pleading', 'exhibit']:
        count = files_query.filter_by(document_type=doc_type).count()
        if count > 0:
            files_by_type[doc_type] = count
    
    return jsonify({
        'cases': {
            'total': total_cases,
            'active': active_cases,
            'pending': pending_cases,
            'closed': closed_cases,
            'by_type': cases_by_type,
            'recent_week': recent_cases
        },
        'files': {
            'total': total_files,
            'recent_week': recent_files,
            'by_type': files_by_type
        },
        'system': {
            'uptime': '99.8%',
            'storage_used': '65%',
            'last_backup': datetime.utcnow().strftime('%Y-%m-%d %H:%M')
        }
    })

@reports_bp.route('/activity', methods=['GET'])
@jwt_required()
def activity_report():
    """Get system activity report"""
    current_user_id = get_jwt_identity()
    current_user = User.query.get(current_user_id)
    
    if not current_user or current_user.role != 'admin':
        return jsonify({'error': 'Admin access required'}), 403
    
    days = int(request.args.get('days', 7))
    start_date = datetime.utcnow() - timedelta(days=days)
    
    # Get audit logs
    logs = AuditLog.query\
        .filter(AuditLog.created_at >= start_date)\
        .order_by(AuditLog.created_at.desc())\
        .limit(100)\
        .all()
    
    # Get user activity
    active_users = User.query\
        .filter(User.last_login >= start_date)\
        .count()
    
    # Get upload activity
    uploads = CaseFile.query\
        .filter(CaseFile.created_at >= start_date)\
        .count()
    
    return jsonify({
        'period': f'Last {days} days',
        'audit_logs': [log.to_dict() for log in logs],
        'metrics': {
            'active_users': active_users,
            'file_uploads': uploads,
            'case_creations': Case.query.filter(Case.created_at >= start_date).count(),
            'user_logins': AuditLog.query.filter(
                AuditLog.action == 'login',
                AuditLog.created_at >= start_date
            ).count()
        }
    })

@reports_bp.route('/export', methods=['POST'])
@jwt_required()
def export_report():
    """Export report data"""
    current_user_id = get_jwt_identity()
    current_user = User.query.get(current_user_id)
    
    if not current_user:
        return jsonify({'error': 'Invalid user'}), 401
    
    data = request.get_json() or {}
    report_type = data.get('type', 'cases')
    
    # Generate report based on type
    if report_type == 'cases':
        query = Case.query
        if current_user.role == 'judge':
            query = query.filter_by(judge_id=current_user_id)
        
        cases = query.all()
        report_data = [case.to_dict() for case in cases]
        
    elif report_type == 'files':
        query = CaseFile.query
        if current_user.role == 'judge':
            query = query.join(Case).filter(Case.judge_id == current_user_id)
        
        files = query.all()
        report_data = [file.to_dict() for file in files]
        
    else:
        return jsonify({'error': 'Invalid report type'}), 400
    
    # Create CSV content (simplified)
    import csv
    import io
    
    output = io.StringIO()
    if report_data:
        # Get headers from first item
        headers = report_data[0].keys()
        writer = csv.DictWriter(output, fieldnames=headers)
        writer.writeheader()
        writer.writerows(report_data)
    
    # Audit the export
    audit_log = AuditLog(
        user_id=current_user_id,
        action='report_export',
        resource_type='report',
        details=f'Exported {report_type} report'
    )
    db.session.add(audit_log)
    db.session.commit()
    
    return jsonify({
        'message': 'Report generated',
        'data': output.getvalue(),
        'type': 'csv'
    })