# department_head_routes.py
from flask import Blueprint, render_template, jsonify, request, redirect, url_for
from flask_login import login_required, current_user
from models import db, DepartmentHead, Client, WellnessAssessment, Notification
from datetime import datetime, timedelta
import json

dept_head_bp = Blueprint('department_head', __name__, url_prefix='/department-head')

@dept_head_bp.before_request
@login_required
def check_department_head():
    if current_user.role != 'department_head':
        return redirect(url_for('main.index'))

@dept_head_bp.route('/dashboard')
def dashboard():
    """Department head dashboard"""
    return render_template('department_head/dashboard.html')

@dept_head_bp.route('/api/dashboard/stats')
def api_dashboard_stats():
    """Get department statistics (anonymized)"""
    dept_head = current_user.department_head_profile
    
    if not dept_head or not dept_head.department:
        return jsonify({'error': 'No department assigned'}), 404
    
    department = dept_head.department
    
    # Get anonymized employee data
    employees = Client.query.filter_by(department_id=department.id).all()
    
    # Calculate statistics
    total_employees = len(employees)
    active_last_30 = sum(1 for e in employees if e.user.last_active and 
                        e.user.last_active > datetime.utcnow() - timedelta(days=30))
    
    # Assessment statistics
    assessments = WellnessAssessment.query.join(Client).filter(
        Client.department_id == department.id
    ).all()
    
    avg_score = sum(a.overall_score for a in assessments) / len(assessments) if assessments else 0
    
    # Risk distribution
    risk_counts = {
        'high': sum(1 for e in employees if e.risk_level == 'high'),
        'medium': sum(1 for e in employees if e.risk_level == 'medium'),
        'low': sum(1 for e in employees if e.risk_level == 'low')
    }
    
    # Recent assessments (anonymized)
    recent_assessments = WellnessAssessment.query.join(Client).filter(
        Client.department_id == department.id
    ).order_by(
        WellnessAssessment.created_at.desc()
    ).limit(20).all()
    
    return jsonify({
        'department': {
            'id': department.id,
            'name': department.name,
            'employee_count': total_employees,
            'active_last_30': active_last_30,
            'average_wellness_score': avg_score,
            'risk_distribution': risk_counts
        },
        'recent_assessments': [{
            'id': a.id,
            'employee_id': a.client_id,  # Just ID, no personal info
            'overall_score': a.overall_score,
            'risk_level': a.risk_level,
            'date': a.created_at.isoformat(),
            'suggested_tests': json.loads(a.suggested_tests) if a.suggested_tests else []
        } for a in recent_assessments],
        'trends': {
            'wellness_over_time': calculate_wellness_trend(department.id),
            'assessment_frequency': calculate_assessment_frequency(department.id)
        }
    })

@dept_head_bp.route('/api/suggest-test', methods=['POST'])
def api_suggest_test():
    """Suggest a test for an employee"""
    data = request.json
    assessment_id = data.get('assessment_id')
    suggested_test = data.get('suggested_test')
    
    assessment = WellnessAssessment.query.get_or_404(assessment_id)
    
    # Verify this employee belongs to department head's department
    if assessment.client.department_id != current_user.department_head_profile.department_id:
        return jsonify({'error': 'Unauthorized'}), 403
    
    # Add suggested test
    current_suggestions = json.loads(assessment.suggested_tests) if assessment.suggested_tests else []
    if suggested_test not in current_suggestions:
        current_suggestions.append(suggested_test)
        assessment.suggested_tests = json.dumps(current_suggestions)
        assessment.suggested_by = current_user.id
        
        db.session.commit()
        
        # Notify employee (anonymously)
        notification = Notification(
            user_id=assessment.client.user_id,
            title='New Test Suggestion',
            message=f'A new test has been suggested for you: {suggested_test}',
            notification_type='info',
            link='/client/assessments'
        )
        db.session.add(notification)
        db.session.commit()
    
    return jsonify({'success': True, 'message': 'Test suggested successfully'})

def calculate_wellness_trend(department_id):
    """Calculate wellness score trend over time"""
    # Group assessments by week and calculate average
    end_date = datetime.now()
    start_date = end_date - timedelta(days=90)
    
    assessments = WellnessAssessment.query.join(Client).filter(
        Client.department_id == department_id,
        WellnessAssessment.created_at >= start_date
    ).all()
    
    # Group by week
    weeks = {}
    for a in assessments:
        week = a.created_at.strftime('%Y-%W')
        if week not in weeks:
            weeks[week] = []
        weeks[week].append(a.overall_score)
    
    trend = [{
        'week': week,
        'avg_score': sum(scores) / len(scores)
    } for week, scores in weeks.items()]
    
    return sorted(trend, key=lambda x: x['week'])

def calculate_assessment_frequency(department_id):
    """Calculate how often employees take assessments"""
    employees = Client.query.filter_by(department_id=department_id).all()
    
    frequency = {
        'very_active': 0,  # > 1 per month
        'active': 0,       # 1 per month
        'moderate': 0,     # 1 per quarter
        'inactive': 0      # none in 3 months
    }
    
    three_months_ago = datetime.utcnow() - timedelta(days=90)
    
    for emp in employees:
        last_assessment = WellnessAssessment.query.filter_by(
            client_id=emp.id
        ).order_by(WellnessAssessment.created_at.desc()).first()
        
        if not last_assessment:
            frequency['inactive'] += 1
        elif last_assessment.created_at > datetime.utcnow() - timedelta(days=30):
            frequency['very_active'] += 1
        elif last_assessment.created_at > datetime.utcnow() - timedelta(days=60):
            frequency['active'] += 1
        elif last_assessment.created_at > three_months_ago:
            frequency['moderate'] += 1
        else:
            frequency['inactive'] += 1
    
    return frequency