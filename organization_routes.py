# organization_routes.py - Complete with proper blueprint name
from flask import Blueprint, render_template, jsonify, request, redirect, url_for
from flask_login import login_required, current_user
from models import db, Organization, Client, Department, DepartmentHead, Session, WellnessAssessment, Notification, User, ActivityLog
from datetime import datetime, timedelta
import json
import secrets

# Create blueprint with the name 'organization_bp' (this matches your import)
organization_bp = Blueprint('organization', __name__, url_prefix='/organization')

@organization_bp.before_request
@login_required
def check_org_access():
    """Check if user has organization role"""
    valid_roles = ['org_manager', 'org_dept_head', 'org_it', 'org_hr', 'organization_admin']
    if current_user.role not in valid_roles:
        return redirect(url_for('main.index'))

@organization_bp.route('/dashboard')
def dashboard():
    """Organization dashboard - role-based view"""
    if current_user.role == 'org_manager':
        return render_template('organization/manager_dashboard.html')
    elif current_user.role == 'org_dept_head':
        return render_template('organization/department_head_dashboard.html')
    elif current_user.role == 'org_it':
        return render_template('organization/it_dashboard.html')
    elif current_user.role == 'org_hr':
        return render_template('organization/hr_dashboard.html')
    elif current_user.role == 'organization_admin':
        return render_template('organization/admin_dashboard.html')
    else:
        return redirect(url_for('employee.dashboard'))

@organization_bp.route('/api/dashboard/data')
def api_dashboard_data():
    """Get organization data based on user role"""
    organization = Organization.query.filter_by(user_id=current_user.id).first()
    if not organization:
        return jsonify({'error': 'Organization not found'}), 404
    
    # Base data - anonymized employee list
    employees = Client.query.filter_by(organization_id=organization.id).all()
    
    # Different data based on role
    if current_user.role == 'org_manager' or current_user.role == 'organization_admin':
        # Manager sees everything but anonymized
        return jsonify(get_manager_data(organization, employees))
    
    elif current_user.role == 'org_dept_head':
        # Department head sees only their department
        dept_head = DepartmentHead.query.filter_by(user_id=current_user.id).first()
        if dept_head and dept_head.department_id:
            dept_employees = [e for e in employees if e.department_id == dept_head.department_id]
            return jsonify(get_department_head_data(organization, dept_head, dept_employees))
        return jsonify({'error': 'Department not assigned'}), 404
    
    elif current_user.role == 'org_it':
        # IT sees only system info and can reset passwords
        return jsonify(get_it_data(organization, employees))
    
    elif current_user.role == 'org_hr':
        # HR sees anonymized employee data and engagement metrics
        return jsonify(get_hr_data(organization, employees))
    
    return jsonify({'error': 'Unauthorized'}), 403

def get_manager_data(organization, employees):
    """Manager view - full organization analytics (anonymized)"""
    
    # Calculate statistics
    total_employees = len(employees)
    active_today = sum(1 for e in employees if e.user.last_active and 
                      e.user.last_active.date() == datetime.utcnow().date())
    active_week = sum(1 for e in employees if e.user.last_active and 
                     e.user.last_active > datetime.utcnow() - timedelta(days=7))
    
    # Session statistics
    total_sessions = Session.query.filter(
        Session.client_id.in_([e.id for e in employees])
    ).count()
    
    sessions_this_month = Session.query.filter(
        Session.client_id.in_([e.id for e in employees]),
        Session.created_at >= datetime.utcnow() - timedelta(days=30)
    ).count()
    
    # Wellness metrics
    avg_wellness = sum(e.wellness_score for e in employees) / total_employees if total_employees > 0 else 0
    
    risk_counts = {
        'high': sum(1 for e in employees if e.risk_level == 'high'),
        'medium': sum(1 for e in employees if e.risk_level == 'medium'),
        'low': sum(1 for e in employees if e.risk_level == 'low')
    }
    
    # Department breakdown
    departments = Department.query.filter_by(organization_id=organization.id).all()
    dept_stats = []
    for dept in departments:
        dept_employees = [e for e in employees if e.department_id == dept.id]
        if dept_employees:
            dept_stats.append({
                'id': dept.id,
                'name': dept.name,
                'employee_count': len(dept_employees),
                'avg_wellness': sum(e.wellness_score for e in dept_employees) / len(dept_employees),
                'high_risk': sum(1 for e in dept_employees if e.risk_level == 'high')
            })
    
    # Recent activity (anonymized)
    recent_activity = ActivityLog.query.filter(
        ActivityLog.user_id.in_([e.user_id for e in employees])
    ).order_by(ActivityLog.created_at.desc()).limit(50).all()
    
    # Service usage
    service_usage = {
        'counseling': Session.query.filter(
            Session.client_id.in_([e.id for e in employees]),
            Session.session_type == 'individual'
        ).count(),
        'group': Session.query.filter(
            Session.client_id.in_([e.id for e in employees]),
            Session.session_type == 'group'
        ).count(),
        'ai_chat': sum(e.assessment_count for e in employees)
    }
    
    return {
        'role': 'manager',
        'organization': {
            'id': organization.id,
            'name': organization.company_name,
            'total_employees': total_employees,
            'active_today': active_today,
            'active_week': active_week,
            'employee_code': organization.employee_registration_code
        },
        'metrics': {
            'total_sessions': total_sessions,
            'sessions_this_month': sessions_this_month,
            'avg_wellness': round(avg_wellness, 2),
            'risk_distribution': risk_counts,
            'service_usage': service_usage
        },
        'departments': dept_stats,
        'recent_activity': [{
            'id': a.id,
            'action': a.action,
            'time': a.created_at.isoformat(),
            'entity_type': a.entity_type
        } for a in recent_activity[:20]],
        'employee_list': [{
            'id': e.id,
            'department_id': e.department_id,
            'wellness_score': e.wellness_score,
            'risk_level': e.risk_level,
            'last_active': e.user.last_active.isoformat() if e.user.last_active else None,
            'assessment_count': e.assessment_count,
            'sessions_attended': len(e.sessions)
        } for e in employees]
    }

def get_department_head_data(organization, dept_head, employees):
    """Department head view - only their department (anonymized)"""
    
    total_employees = len(employees)
    
    if total_employees == 0:
        return {
            'role': 'department_head',
            'department': {
                'id': dept_head.department.id,
                'name': dept_head.department.name,
                'employee_count': 0
            },
            'metrics': {
                'avg_wellness': 0,
                'high_risk': 0,
                'medium_risk': 0,
                'low_risk': 0
            },
            'recent_assessments': []
        }
    
    # Department metrics
    avg_wellness = sum(e.wellness_score for e in employees) / total_employees
    
    risk_counts = {
        'high': sum(1 for e in employees if e.risk_level == 'high'),
        'medium': sum(1 for e in employees if e.risk_level == 'medium'),
        'low': sum(1 for e in employees if e.risk_level == 'low')
    }
    
    # Recent assessments in department
    recent_assessments = WellnessAssessment.query.filter(
        WellnessAssessment.client_id.in_([e.id for e in employees])
    ).order_by(WellnessAssessment.created_at.desc()).limit(20).all()
    
    return {
        'role': 'department_head',
        'department': {
            'id': dept_head.department.id,
            'name': dept_head.department.name,
            'employee_count': total_employees
        },
        'metrics': {
            'avg_wellness': round(avg_wellness, 2),
            'high_risk': risk_counts['high'],
            'medium_risk': risk_counts['medium'],
            'low_risk': risk_counts['low']
        },
        'recent_assessments': [{
            'id': a.id,
            'score': a.overall_score,
            'risk': a.risk_level,
            'date': a.created_at.isoformat(),
            'suggested_tests': json.loads(a.suggested_tests) if a.suggested_tests else []
        } for a in recent_assessments],
        'employee_stats': [{
            'id': e.id,
            'wellness_score': e.wellness_score,
            'risk_level': e.risk_level,
            'last_active': e.user.last_active.isoformat() if e.user.last_active else None
        } for e in employees]
    }

def get_it_data(organization, employees):
    """IT support view - system management and password resets"""
    
    return {
        'role': 'it_support',
        'organization': {
            'id': organization.id,
            'name': organization.company_name,
            'employee_count': len(employees),
            'employee_code': organization.employee_registration_code
        },
        'system_stats': {
            'active_users_today': sum(1 for e in employees if e.user.last_active and 
                                     e.user.last_active.date() == datetime.utcnow().date()),
            'total_logins': ActivityLog.query.filter(
                ActivityLog.user_id.in_([e.user_id for e in employees]),
                ActivityLog.action == 'LOGIN'
            ).count(),
            'password_resets_this_month': ActivityLog.query.filter(
                ActivityLog.user_id.in_([e.user_id for e in employees]),
                ActivityLog.action == 'PASSWORD_RESET',
                ActivityLog.created_at >= datetime.utcnow() - timedelta(days=30)
            ).count()
        },
        'employees': [{
            'id': e.id,
            'user_id': e.user_id,
            'email': e.user.email,  # IT needs email for password resets
            'last_login': e.user.last_login.isoformat() if e.user.last_login else None,
            'account_status': 'active' if e.user.is_active else 'inactive'
        } for e in employees]
    }

def get_hr_data(organization, employees):
    """HR view - engagement and wellness metrics (anonymized)"""
    
    total_employees = len(employees)
    
    # Engagement metrics
    active_this_month = sum(1 for e in employees if e.user.last_active and 
                          e.user.last_active > datetime.utcnow() - timedelta(days=30))
    
    # Assessment completion rate
    employees_with_assessments = sum(1 for e in employees if e.assessment_count > 0)
    assessment_rate = (employees_with_assessments / total_employees * 100) if total_employees > 0 else 0
    
    # Session utilization
    total_sessions = Session.query.filter(
        Session.client_id.in_([e.id for e in employees])
    ).count()
    
    sessions_per_employee = total_sessions / total_employees if total_employees > 0 else 0
    
    # Wellness trends over time
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)
    assessments_last_month = WellnessAssessment.query.filter(
        WellnessAssessment.client_id.in_([e.id for e in employees]),
        WellnessAssessment.created_at >= thirty_days_ago
    ).all()
    
    avg_scores = [a.overall_score for a in assessments_last_month]
    avg_trend = sum(avg_scores) / len(avg_scores) if avg_scores else 0
    
    return {
        'role': 'hr_manager',
        'organization': {
            'id': organization.id,
            'name': organization.company_name,
            'total_employees': total_employees
        },
        'engagement': {
            'active_this_month': active_this_month,
            'active_percentage': round(active_this_month / total_employees * 100, 2) if total_employees > 0 else 0,
            'assessment_rate': round(assessment_rate, 2),
            'sessions_per_employee': round(sessions_per_employee, 2)
        },
        'wellness': {
            'current_avg': organization.average_wellness_score,
            'trend_avg': round(avg_trend, 2),
            'high_risk': organization.high_risk_employees,
            'medium_risk': organization.medium_risk_employees,
            'low_risk': organization.low_risk_employees
        },
        'department_summary': [{
            'id': d.id,
            'name': d.name,
            'employee_count': d.employee_count,
            'avg_wellness': d.average_wellness_score,
            'high_risk': d.high_risk_count
        } for d in Department.query.filter_by(organization_id=organization.id).all()]
    }

@organization_bp.route('/api/reset-password', methods=['POST'])
@login_required
def api_reset_password():
    """IT Support - Reset employee password"""
    if current_user.role != 'org_it':
        return jsonify({'error': 'Unauthorized'}), 403
    
    data = request.json
    employee_id = data.get('employee_id')
    new_password = data.get('new_password')
    
    if not new_password or len(new_password) < 8:
        return jsonify({'success': False, 'message': 'Password must be at least 8 characters'}), 400
    
    employee = Client.query.get_or_404(employee_id)
    
    # Verify employee belongs to same organization
    org = Organization.query.filter_by(user_id=current_user.id).first()
    if employee.organization_id != org.id:
        return jsonify({'error': 'Unauthorized'}), 403
    
    # Reset password
    user = User.query.get(employee.user_id)
    user.set_password(new_password)
    
    # Log activity
    log = ActivityLog(
        user_id=current_user.id,
        action='PASSWORD_RESET',
        description=f'IT support reset password for employee {employee.id}',
        entity_type='employee',
        entity_id=employee.id
    )
    db.session.add(log)
    db.session.commit()
    
    return jsonify({'success': True, 'message': 'Password reset successfully'})

@organization_bp.route('/api/update-organization', methods=['POST'])
@login_required
def api_update_organization():
    """Update organization settings"""
    if current_user.role not in ['org_manager', 'organization_admin']:
        return jsonify({'error': 'Unauthorized'}), 403
    
    data = request.json
    organization = Organization.query.filter_by(user_id=current_user.id).first()
    
    if not organization:
        return jsonify({'error': 'Organization not found'}), 404
    
    # Update fields
    if 'company_name' in data:
        organization.company_name = data['company_name']
    if 'industry' in data:
        organization.industry = data['industry']
    if 'anonymize_employee_data' in data:
        organization.anonymize_employee_data = data['anonymize_employee_data']
    
    db.session.commit()
    
    return jsonify({'success': True, 'message': 'Organization updated successfully'})

@organization_bp.route('/api/generate-new-code', methods=['POST'])
@login_required
def api_generate_new_code():
    """Generate new employee registration code"""
    if current_user.role not in ['org_manager', 'organization_admin', 'org_it']:
        return jsonify({'error': 'Unauthorized'}), 403
    
    organization = Organization.query.filter_by(user_id=current_user.id).first()
    
    if not organization:
        return jsonify({'error': 'Organization not found'}), 404
    
    # Generate new code
    new_code = secrets.token_hex(4).upper()
    organization.employee_registration_code = new_code
    db.session.commit()
    
    return jsonify({
        'success': True,
        'message': 'New employee code generated',
        'employee_code': new_code
    })
