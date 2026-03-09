# professional_routes.py
from flask import Blueprint, render_template, jsonify, request
from flask_login import login_required, current_user
from models import db, Professional, Session, SessionRequest, Webinar, Notification
from datetime import datetime, timedelta

professional_bp = Blueprint('professional', __name__, url_prefix='/professional')

@professional_bp.route('/dashboard')
@login_required
def dashboard():
    if not current_user.is_professional:
        return redirect(url_for('main.index'))
    return render_template('professional/dashboard.html')

@professional_bp.route('/api/dashboard/stats')
@login_required
def api_dashboard_stats():
    if not current_user.is_professional:
        return jsonify({'error': 'Unauthorized'}), 403
    
    professional = current_user.professional_profile
    
    # Get stats
    total_sessions = Session.query.filter_by(professional_id=professional.id).count()
    upcoming_sessions = Session.query.filter_by(
        professional_id=professional.id,
        status='scheduled'
    ).filter(
        Session.scheduled_date >= datetime.now().date()
    ).count()
    
    pending_requests = SessionRequest.query.filter_by(
        professional_id=professional.id,
        status='matched'
    ).count()
    
    total_earnings = db.session.query(db.func.sum(Session.professional_fee)).filter_by(
        professional_id=professional.id,
        status='completed'
    ).scalar() or 0
    
    return jsonify({
        'total_sessions': total_sessions,
        'upcoming_sessions': upcoming_sessions,
        'pending_requests': pending_requests,
        'total_earnings': total_earnings,
        'rating': professional.average_rating
    })

@professional_bp.route('/api/session-requests')
@login_required
def api_session_requests():
    if not current_user.is_professional:
        return jsonify({'error': 'Unauthorized'}), 403
    
    professional = current_user.professional_profile
    
    requests = SessionRequest.query.filter_by(
        professional_id=professional.id,
        status='matched'
    ).all()
    
    return jsonify([{
        'id': r.id,
        'client_name': 'Anonymous' if r.client.user.get_full_name() else 'Client',
        'issue': r.issue_description[:100] + '...',
        'preferred_date': r.preferred_date.isoformat() if r.preferred_date else None,
        'preferred_time': r.preferred_time,
        'expires_at': r.expires_at.isoformat(),
        'time_remaining': (r.expires_at - datetime.utcnow()).seconds // 60
    } for r in requests])

@professional_bp.route('/api/confirm-request/<int:request_id>', methods=['POST'])
@login_required
def api_confirm_request(request_id):
    if not current_user.is_professional:
        return jsonify({'error': 'Unauthorized'}), 403
    
    professional = current_user.professional_profile
    session_request = SessionRequest.query.get_or_404(request_id)
    
    if session_request.professional_id != professional.id:
        return jsonify({'error': 'Not authorized'}), 403
    
    # Create session
    session = Session(
        client_id=session_request.client_id,
        professional_id=professional.id,
        request_id=session_request.id,
        session_type=session_request.session_type,
        scheduled_date=session_request.preferred_date or datetime.now().date(),
        scheduled_time=session_request.preferred_time or '09:00',
        professional_fee=professional.session_fee,
        platform_fee=professional.session_fee * 0.2,
        total_fee=professional.session_fee * 1.2,
        status='scheduled'
    )
    
    # Update request
    session_request.status = 'confirmed'
    
    db.session.add(session)
    db.session.commit()
    
    # Notify client
    notification = Notification(
        user_id=session_request.client.user_id,
        title='Session Confirmed',
        message=f'Your session has been confirmed by {professional.user.get_full_name()}',
        notification_type='success'
    )
    db.session.add(notification)
    db.session.commit()
    
    return jsonify({'success': True})

@professional_bp.route('/api/create-webinar', methods=['POST'])
@login_required
def api_create_webinar():
    if not current_user.is_professional:
        return jsonify({'error': 'Unauthorized'}), 403
    
    data = request.json
    professional = current_user.professional_profile
    
    webinar = Webinar(
        professional_id=professional.id,
        title=data['title'],
        description=data['description'],
        topic=data['topic'],
        scheduled_date=datetime.strptime(data['date'], '%Y-%m-%d').date(),
        scheduled_time=data['time'],
        duration_minutes=data.get('duration', 60),
        max_participants=data.get('max_participants', 50),
        is_free=data.get('is_free', True),
        fee=data.get('fee', 0)
    )
    
    db.session.add(webinar)
    db.session.commit()
    
    return jsonify({'success': True, 'webinar_id': webinar.id})