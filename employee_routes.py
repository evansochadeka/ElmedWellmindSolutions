# employee_routes.py

from flask import Blueprint, render_template, jsonify, request
from flask_login import login_required, current_user
from models import db, Client, Organization, Department, Professional, Session, WellnessAssessment, Notification
from datetime import datetime, timedelta
import json

employee_bp = Blueprint('employee', __name__, url_prefix='/employee')

@employee_bp.before_request
@login_required
def check_employee():
    if current_user.role != 'org_employee':
        return redirect(url_for('main.index'))

@employee_bp.route('/dashboard')
def dashboard():
    """Employee dashboard"""
    return render_template('employee/dashboard.html')

@employee_bp.route('/api/dashboard/data')
def api_dashboard_data():
    """Get employee dashboard data"""
    employee = Client.query.filter_by(user_id=current_user.id).first()
    if not employee:
        return jsonify({'error': 'Employee profile not found'}), 404
    
    organization = Organization.query.get(employee.organization_id)
    
    # Get upcoming sessions
    upcoming_sessions = Session.query.filter_by(
        client_id=employee.id,
        status='scheduled'
    ).filter(
        Session.scheduled_date >= datetime.now().date()
    ).order_by(Session.scheduled_date).all()
    
    # Get past sessions
    past_sessions = Session.query.filter_by(
        client_id=employee.id
    ).filter(
        Session.scheduled_date < datetime.now().date()
    ).order_by(Session.scheduled_date.desc()).limit(5).all()
    
    # Get available professionals
    professionals = Professional.query.filter_by(
        is_verified=True,
        is_available=True,
        accepting_clients=True
    ).limit(10).all()
    
    # Get recent assessments
    assessments = WellnessAssessment.query.filter_by(
        client_id=employee.id
    ).order_by(WellnessAssessment.created_at.desc()).limit(5).all()
    
    # Calculate progress
    assessment_scores = [a.overall_score for a in assessments]
    progress = {
        'current': employee.wellness_score,
        'previous': assessment_scores[1] if len(assessment_scores) > 1 else employee.wellness_score,
        'improvement': employee.wellness_score - (assessment_scores[1] if len(assessment_scores) > 1 else employee.wellness_score)
    }
    
    # Get notifications
    notifications = Notification.query.filter_by(
        user_id=current_user.id,
        is_read=False
    ).order_by(Notification.created_at.desc()).all()
    
    return jsonify({
        'organization': {
            'id': organization.id,
            'name': organization.company_name,
            'department': employee.department
        },
        'employee': {
            'id': employee.id,
            'wellness_score': employee.wellness_score,
            'risk_level': employee.risk_level,
            'assessment_count': employee.assessment_count,
            'joined_date': employee.created_at.strftime('%B %Y')
        },
        'upcoming_sessions': [{
            'id': s.id,
            'title': s.title,
            'date': s.scheduled_date.strftime('%Y-%m-%d'),
            'time': s.scheduled_time,
            'professional': s.professional.user.get_full_name() if s.professional else 'TBD',
            'meeting_link': s.meeting_link
        } for s in upcoming_sessions],
        'past_sessions': [{
            'id': s.id,
            'title': s.title,
            'date': s.scheduled_date.strftime('%Y-%m-%d'),
            'professional': s.professional.user.get_full_name() if s.professional else 'TBD',
            'status': s.status
        } for s in past_sessions],
        'professionals': [{
            'id': p.id,
            'name': p.user.get_full_name(),
            'type': p.professional_type,
            'specializations': p.get_specializations(),
            'rating': p.average_rating,
            'fee': p.client_facing_fee,
            'available': p.is_available
        } for p in professionals],
        'assessments': [{
            'id': a.id,
            'score': a.overall_score,
            'date': a.created_at.strftime('%Y-%m-%d'),
            'risk': a.risk_level
        } for a in assessments],
        'progress': progress,
        'notifications': [{
            'id': n.id,
            'title': n.title,
            'message': n.message,
            'time': n.created_at.isoformat()
        } for n in notifications],
        'services_accessed': {
            'counseling': len([s for s in past_sessions if s.session_type == 'individual']),
            'group': len([s for s in past_sessions if s.session_type == 'group']),
            'assessments': employee.assessment_count
        }
    })

@employee_bp.route('/api/book-session', methods=['POST'])
def api_book_session():
    """Book a session with a professional"""
    data = request.json
    employee = Client.query.filter_by(user_id=current_user.id).first()
    
    session = Session(
        client_id=employee.id,
        professional_id=data.get('professional_id'),
        session_type=data.get('session_type', 'individual'),
        title=data.get('title', 'Counseling Session'),
        scheduled_date=datetime.strptime(data['date'], '%Y-%m-%d').date(),
        scheduled_time=data['time'],
        status='scheduled'
    )
    
    db.session.add(session)
    db.session.commit()
    
    return jsonify({'success': True, 'message': 'Session booked successfully'})

@employee_bp.route('/api/take-assessment', methods=['POST'])
def api_take_assessment():
    """Submit a wellness assessment"""
    data = request.json
    employee = Client.query.filter_by(user_id=current_user.id).first()
    
    # Calculate scores (simplified - implement actual logic)
    overall_score = data.get('overall_score', 0)
    
    assessment = WellnessAssessment(
        client_id=employee.id,
        responses=json.dumps(data.get('responses', {})),
        overall_score=overall_score,
        risk_level='low' if overall_score > 70 else 'medium' if overall_score > 40 else 'high'
    )
    
    db.session.add(assessment)
    
    # Update employee stats
    employee.wellness_score = (employee.wellness_score * employee.assessment_count + overall_score) / (employee.assessment_count + 1)
    employee.assessment_count += 1
    employee.last_assessment = datetime.utcnow()
    
    # Update risk level
    if employee.wellness_score > 70:
        employee.risk_level = 'low'
    elif employee.wellness_score > 40:
        employee.risk_level = 'medium'
    else:
        employee.risk_level = 'high'
    
    db.session.commit()
    
    return jsonify({
        'success': True,
        'message': 'Assessment submitted successfully',
        'score': overall_score,
        'risk_level': employee.risk_level
    })