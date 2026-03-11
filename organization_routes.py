# organization_routes.py - COMPLETE WITH ALL ORGANIZATION ROLES
from flask import Blueprint, render_template, jsonify, request, redirect, url_for
from flask_login import login_required, current_user
from models import db, Organization, Client, Department, DepartmentHead, Professional, Session, WellnessAssessment, Notification, Complaint
from datetime import datetime, timedelta
import json

organization_bp = Blueprint('organization', __name__, url_prefix='/organization')

# ========== ROLE-BASED ACCESS CONTROL ==========

@organization_bp.before_request
@login_required
def check_org_access():
    """Check if user has organization role"""
    allowed_roles = ['organization_admin', 'org_manager', 'org_hr', 'org_supervisor']
    if current_user.role not in allowed_roles:
        return redirect(url_for('main.index'))

def get_organization():
    """Get organization for current user based on role"""
    if current_user.role == 'organization_admin':
        return Organization.query.filter_by(user_id=current_user.id).first()
    elif current_user.role in ['org_manager', 'org_hr', 'org_supervisor']:
        # For managers/HR/supervisors, get org from their employee profile
        client = Client.query.filter_by(user_id=current_user.id).first()
        if client:
            return Organization.query.get(client.organization_id)
    return None

# ========== DASHBOARD ROUTES ==========

@organization_bp.route('/dashboard')
@login_required
def dashboard():
    """Organization dashboard - role-based view"""
    org = get_organization()
    if not org:
        return redirect(url_for('main.index'))
    
    # Different dashboards for different roles
    if current_user.role == 'organization_admin':
        return render_template('organization/admin_dashboard.html', organization=org)
    elif current_user.role == 'org_manager':
        return render_template('organization/manager_dashboard.html', organization=org)
    elif current_user.role == 'org_hr':
        return render_template('organization/hr_dashboard.html', organization=org)
    elif current_user.role == 'org_supervisor':
        return render_template('organization/supervisor_dashboard.html', organization=org)
    else:
        return render_template('organization/dashboard.html', organization=org)

# ========== API ENDPOINTS ==========

@organization_bp.route('/api/dashboard/data')
@login_required
def api_dashboard_data():
    """Get organization data based on user role"""
    org = get_organization()
    if not org:
        return jsonify({'error': 'Organization not found'}), 404
    
    employees = Client.query.filter_by(organization_id=org.id).all()
    
    # Base stats for all roles
    total_employees = len(employees)
    active_today = sum(1 for e in employees if e.user.last_active and 
                      e.user.last_active.date() == datetime.now().date())
    
    total_sessions = Session.query.filter(
        Session.client_id.in_([e.id for e in employees])
    ).count()
    
    avg_wellness = sum(e.wellness_score for e in employees) / total_employees if total_employees > 0 else 0
    
    # Department breakdown
    departments = Department.query.filter_by(organization_id=org.id).all()
    dept_data = []
    for dept in departments:
        dept_employees = [e for e in employees if e.department_id == dept.id]
        dept_data.append({
            'id': dept.id,
            'name': dept.name,
            'employee_count': len(dept_employees),
            'avg_wellness': sum(e.wellness_score for e in dept_employees) / len(dept_employees) if dept_employees else 0,
            'high_risk': sum(1 for e in dept_employees if e.risk_level == 'high'),
            'medium_risk': sum(1 for e in dept_employees if e.risk_level == 'medium'),
            'low_risk': sum(1 for e in dept_employees if e.risk_level == 'low'),
            'active_today': sum(1 for e in dept_employees if e.user.last_active and 
                               e.user.last_active.date() == datetime.now().date())
        })
    
    # Role-specific data
    if current_user.role == 'organization_admin':
        # Admin sees everything
        return jsonify({
            'role': 'admin',
            'stats': {
                'total_employees': total_employees,
                'active_today': active_today,
                'total_sessions': total_sessions,
                'avg_wellness': avg_wellness,
                'employee_code': org.employee_registration_code
            },
            'departments': dept_data,
            'employees': [{
                'id': e.id,
                'department': e.department.name if e.department else None,
                'wellness_score': e.wellness_score,
                'risk_level': e.risk_level,
                'last_active': e.user.last_active.isoformat() if e.user.last_active else None,
                'sessions': len(e.sessions),
                'assessments': e.assessment_count
            } for e in employees]
        })
    
    elif current_user.role == 'org_manager':
        # Manager sees aggregated data
        return jsonify({
            'role': 'manager',
            'stats': {
                'total_employees': total_employees,
                'active_today': active_today,
                'total_sessions': total_sessions,
                'avg_wellness': avg_wellness,
                'high_risk': sum(1 for e in employees if e.risk_level == 'high')
            },
            'departments': dept_data,
            'recent_activity': []  # Add recent activity
        })
    
    elif current_user.role == 'org_hr':
        # HR sees wellness and engagement data
        return jsonify({
            'role': 'hr',
            'stats': {
                'total_employees': total_employees,
                'active_today': active_today,
                'avg_wellness': avg_wellness,
                'assessments_completed': sum(e.assessment_count for e in employees),
                'high_risk': sum(1 for e in employees if e.risk_level == 'high'),
                'medium_risk': sum(1 for e in employees if e.risk_level == 'medium'),
                'low_risk': sum(1 for e in employees if e.risk_level == 'low')
            },
            'departments': [{
                'name': d.name,
                'avg_wellness': d.average_wellness_score,
                'employee_count': d.employee_count,
                'high_risk': d.high_risk_count
            } for d in departments]
        })
    
    elif current_user.role == 'org_supervisor':
        # Supervisor sees only their department
        supervisor = Client.query.filter_by(user_id=current_user.id).first()
        if supervisor and supervisor.department_id:
            dept_employees = [e for e in employees if e.department_id == supervisor.department_id]
            return jsonify({
                'role': 'supervisor',
                'department': {
                    'id': supervisor.department.id,
                    'name': supervisor.department.name,
                    'employee_count': len(dept_employees),
                    'avg_wellness': sum(e.wellness_score for e in dept_employees) / len(dept_employees) if dept_employees else 0,
                    'high_risk': sum(1 for e in dept_employees if e.risk_level == 'high')
                },
                'employees': [{
                    'id': e.id,
                    'wellness_score': e.wellness_score,
                    'risk_level': e.risk_level,
                    'last_active': e.user.last_active.isoformat() if e.user.last_active else None,
                    'sessions': len(e.sessions)
                } for e in dept_employees]
            })
    
    return jsonify({'error': 'Unauthorized'}), 403

@organization_bp.route('/api/professionals')
@login_required
def api_professionals():
    """Get all verified professionals"""
    professionals = Professional.query.filter_by(is_verified=True).all()
    
    return jsonify([{
        'id': p.id,
        'name': p.user.get_full_name(),
        'profile_pic': p.user.profile_pic,
        'type': p.professional_type,
        'specializations': p.get_specializations(),
        'years_experience': p.years_experience,
        'license_number': p.license_number,
        'average_rating': p.average_rating,
        'total_sessions': p.total_sessions,
        'response_rate': p.response_rate,
        'bio': p.user.bio,
        'session_fee': p.client_facing_fee
    } for p in professionals])

@organization_bp.route('/api/professionals/<int:professional_id>')
@login_required
def api_professional_detail(professional_id):
    """Get professional details"""
    professional = Professional.query.get_or_404(professional_id)
    
    # Get reviews
    reviews = Review.query.filter_by(reviewee_id=professional.user_id).all()
    
    return jsonify({
        'id': professional.id,
        'name': professional.user.get_full_name(),
        'profile_pic': professional.user.profile_pic,
        'type': professional.professional_type,
        'specializations': professional.get_specializations(),
        'years_experience': professional.years_experience,
        'license_number': professional.license_number,
        'average_rating': professional.average_rating,
        'bio': professional.user.bio,
        'total_sessions': professional.total_sessions,
        'response_rate': professional.response_rate,
        'reviews': [{
            'reviewer_name': r.reviewer.get_full_name(),
            'rating': r.rating,
            'comment': r.comment,
            'created_at': r.created_at.isoformat()
        } for r in reviews[:5]]
    })

@organization_bp.route('/api/submit-complaint', methods=['POST'])
@login_required
def api_submit_complaint():
    """Submit complaint about a professional"""
    data = request.json
    org = get_organization()
    
    if not org:
        return jsonify({'success': False, 'message': 'Organization not found'}), 404
    
    complaint = Complaint(
        organization_id=org.id,
        professional_id=data['professional_id'],
        type=data['type'],
        description=data['description'],
        status='pending'
    )
    db.session.add(complaint)
    
    # Notify superadmin
    admins = User.query.filter_by(role='superadmin').all()
    for admin in admins:
        notification = Notification(
            user_id=admin.id,
            title='New Complaint',
            message=f'Complaint from {org.company_name}',
            notification_type='warning',
            link='/superadmin/complaints'
        )
        db.session.add(notification)
    
    db.session.commit()
    
    return jsonify({'success': True, 'message': 'Complaint submitted successfully'})

@organization_bp.route('/api/complaints')
@login_required
def api_complaints():
    """Get organization's complaints"""
    org = get_organization()
    if not org:
        return jsonify([]), 404
    
    complaints = Complaint.query.filter_by(organization_id=org.id)\
                    .order_by(Complaint.created_at.desc()).all()
    
    return jsonify([{
        'id': c.id,
        'professional_name': c.professional.user.get_full_name() if c.professional else 'Unknown',
        'type': c.type,
        'description': c.description,
        'status': c.status,
        'response': c.response,
        'created_at': c.created_at.isoformat()
    } for c in complaints])

@organization_bp.route('/api/departments')
@login_required
def api_departments():
    """Get all departments in organization"""
    org = get_organization()
    if not org:
        return jsonify([]), 404
    
    departments = Department.query.filter_by(organization_id=org.id).all()
    
    return jsonify([{
        'id': d.id,
        'name': d.name,
        'employee_count': d.employee_count,
        'avg_wellness': d.average_wellness_score,
        'high_risk': d.high_risk_count,
        'medium_risk': d.medium_risk_count,
        'low_risk': d.low_risk_count
    } for d in departments])

@organization_bp.route('/api/departments/create', methods=['POST'])
@login_required
def api_create_department():
    """Create new department (admin only)"""
    if current_user.role != 'organization_admin':
        return jsonify({'success': False, 'message': 'Unauthorized'}), 403
    
    data = request.json
    org = get_organization()
    
    dept = Department(
        organization_id=org.id,
        name=data['name'],
        description=data.get('description', '')
    )
    db.session.add(dept)
    db.session.commit()
    
    return jsonify({'success': True, 'department': {
        'id': dept.id,
        'name': dept.name
    }})

@organization_bp.route('/api/employees')
@login_required
def api_employees():
    """Get employees based on role permissions"""
    org = get_organization()
    if not org:
        return jsonify([]), 404
    
    employees = Client.query.filter_by(organization_id=org.id).all()
    
    # Different data exposure based on role
    if current_user.role == 'organization_admin':
        # Admin sees everything
        return jsonify([{
            'id': e.id,
            'department': e.department.name if e.department else None,
            'wellness_score': e.wellness_score,
            'risk_level': e.risk_level,
            'last_active': e.user.last_active.isoformat() if e.user.last_active else None,
            'sessions': len(e.sessions),
            'assessments': e.assessment_count
        } for e in employees])
    
    elif current_user.role == 'org_manager':
        # Manager sees anonymized data
        return jsonify([{
            'id': f"EMP-{e.id}",
            'department': e.department.name if e.department else None,
            'wellness_score': e.wellness_score,
            'risk_level': e.risk_level,
            'last_active': e.user.last_active.isoformat() if e.user.last_active else None
        } for e in employees])
    
    elif current_user.role == 'org_hr':
        # HR sees wellness data only
        return jsonify([{
            'department': e.department.name if e.department else None,
            'wellness_score': e.wellness_score,
            'risk_level': e.risk_level,
            'assessments': e.assessment_count
        } for e in employees])
    
    return jsonify([])

@organization_bp.route('/api/sessions')
@login_required
def api_sessions():
    """Get organization's sessions"""
    org = get_organization()
    if not org:
        return jsonify([]), 404
    
    employees = Client.query.filter_by(organization_id=org.id).all()
    employee_ids = [e.id for e in employees]
    
    upcoming = Session.query.filter(
        Session.client_id.in_(employee_ids),
        Session.status == 'scheduled'
    ).filter(
        Session.scheduled_date >= datetime.now().date()
    ).order_by(Session.scheduled_date).all()
    
    past = Session.query.filter(
        Session.client_id.in_(employee_ids)
    ).filter(
        Session.scheduled_date < datetime.now().date()
    ).order_by(Session.scheduled_date.desc()).limit(50).all()
    
    return jsonify({
        'upcoming': [{
            'id': s.id,
            'employee_id': s.client_id,
            'date': s.scheduled_date.isoformat(),
            'time': s.scheduled_time,
            'professional': s.professional.user.get_full_name() if s.professional else 'Unknown'
        } for s in upcoming],
        'past': [{
            'id': s.id,
            'date': s.scheduled_date.isoformat(),
            'professional': s.professional.user.get_full_name() if s.professional else 'Unknown'
        } for s in past]
    })

@organization_bp.route('/api/analytics')
@login_required
def api_analytics():
    """Get organization analytics (admin only)"""
    if current_user.role != 'organization_admin':
        return jsonify({'error': 'Unauthorized'}), 403
    
    org = get_organization()
    employees = Client.query.filter_by(organization_id=org.id).all()
    
    # Wellness trends over time
    thirty_days_ago = datetime.now() - timedelta(days=30)
    assessments = WellnessAssessment.query.filter(
        WellnessAssessment.client_id.in_([e.id for e in employees]),
        WellnessAssessment.created_at >= thirty_days_ago
    ).all()
    
    # Group by day
    trend_data = {}
    for a in assessments:
        date = a.created_at.date().isoformat()
        if date not in trend_data:
            trend_data[date] = []
        trend_data[date].append(a.overall_score)
    
    wellness_trend = [{
        'date': date,
        'avg_score': sum(scores) / len(scores)
    } for date, scores in trend_data.items()]
    
    # Department comparison
    dept_comparison = []
    departments = Department.query.filter_by(organization_id=org.id).all()
    for dept in departments:
        dept_employees = [e for e in employees if e.department_id == dept.id]
        if dept_employees:
            dept_comparison.append({
                'name': dept.name,
                'avg_wellness': sum(e.wellness_score for e in dept_employees) / len(dept_employees),
                'employee_count': len(dept_employees),
                'high_risk': sum(1 for e in dept_employees if e.risk_level == 'high')
            })
    
    return jsonify({
        'wellness_trend': wellness_trend,
        'department_comparison': dept_comparison,
        'total_sessions': Session.query.filter(
            Session.client_id.in_([e.id for e in employees])
        ).count(),
        'avg_wellness': org.average_wellness_score,
        'high_risk_count': org.high_risk_employees
    })
