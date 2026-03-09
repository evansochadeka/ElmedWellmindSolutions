# organization_routes.py
from flask import Blueprint, render_template, jsonify, request
from flask_login import login_required, current_user
from models import db, Organization, Client, Department, OrganizationWellnessData, Notification
from datetime import datetime, timedelta
import json

organization_bp = Blueprint('organization', __name__, url_prefix='/organization')

@organization_bp.route('/dashboard')
@login_required
def dashboard():
    if not current_user.is_organization:
        return redirect(url_for('main.index'))
    return render_template('organization/dashboard.html')

@organization_bp.route('/api/dashboard/data')
@login_required
def api_dashboard_data():
    if not current_user.is_organization:
        return jsonify({'error': 'Unauthorized'}), 403
    
    org = current_user.organization_profile
    
    # Get employees
    employees = Client.query.filter_by(organization_id=org.id).all()
    
    # Calculate stats
    active_this_month = sum(1 for e in employees if e.user.last_active and e.user.last_active > datetime.utcnow() - timedelta(days=30))
    
    total_sessions = db.session.query(db.func.sum(OrganizationWellnessData.total_sessions)).filter_by(
        organization_id=org.id
    ).scalar() or 0
    
    # Department wellness heatmap
    departments = Department.query.filter_by(organization_id=org.id).all()
    dept_wellness = []
    for dept in departments:
        dept_employees = Client.query.filter_by(organization_id=org.id, department=dept.name).all()
        avg_score = sum(e.wellness_score for e in dept_employees) / len(dept_employees) if dept_employees else 0
        dept_wellness.append({
            'name': dept.name,
            'score': avg_score,
            'employee_count': len(dept_employees),
            'high_risk': sum(1 for e in dept_employees if e.risk_level == 'high')
        })
    
    # High risk employees
    high_risk = [e for e in employees if e.risk_level == 'high']
    
    # Wellness trends (last 6 months)
    trends = []
    for i in range(5, -1, -1):
        month = (datetime.now() - timedelta(days=30*i)).strftime('%Y-%m')
        data = OrganizationWellnessData.query.filter_by(
            organization_id=org.id,
            month=month
        ).first()
        trends.append({
            'month': month,
            'score': data.average_wellness_score if data else 0
        })
    
    # Intervention recommendations
    recommendations = []
    if high_risk:
        recommendations.append({
            'type': 'crisis',
            'message': f'{len(high_risk)} employees need immediate attention',
            'action': 'Schedule one-on-one sessions'
        })
    
    if dept_wellness:
        worst_dept = min(dept_wellness, key=lambda x: x['score'])
        if worst_dept['score'] < 3:
            recommendations.append({
                'type': 'workshop',
                'message': f'Department "{worst_dept["name"]}" has low wellness scores',
                'action': 'Schedule wellness workshop'
            })
    
    return jsonify({
        'stats': {
            'total_employees': len(employees),
            'active_this_month': active_this_month,
            'total_sessions': total_sessions,
            'average_wellness_score': org.average_wellness_score,
            'high_risk_employees': org.high_risk_employees
        },
        'department_wellness': dept_wellness,
        'high_risk_employees': [{
            'name': e.user.get_full_name(),
            'department': e.department,
            'wellness_score': e.wellness_score,
            'last_active': e.user.last_active.isoformat() if e.user.last_active else None
        } for e in high_risk],
        'wellness_trends': trends,
        'recommendations': recommendations,
        'employee_code': org.employee_registration_code
    })

@organization_bp.route('/api/download-report', methods=['POST'])
@login_required
def api_download_report():
    if not current_user.is_organization:
        return jsonify({'error': 'Unauthorized'}), 403
    
    data = request.json
    report_type = data.get('type')
    date_range = data.get('date_range', 'month')
    
    # Generate report (CSV/PDF)
    # This would generate and return a file
    
    return jsonify({'success': True, 'download_url': f'/reports/{report_type}_{date_range}.csv'})