# superadmin_routes.py
from flask import Blueprint, render_template, jsonify, request, redirect, url_for, session
from flask_login import login_required, current_user
from models import db, User, Professional, Organization, Client, Department, DepartmentHead, Session, SessionRequest, Notification, ActivityLog, WellnessAssessment
from datetime import datetime, timedelta
import json

superadmin_bp = Blueprint('superadmin', __name__, url_prefix='/superadmin')

# Middleware to check superadmin access
@superadmin_bp.before_request
@login_required
def check_superadmin():
    if current_user.role != 'superadmin':
        return redirect(url_for('main.index'))

@superadmin_bp.route('/dashboard')
def dashboard():
    """Superadmin main dashboard"""
    return render_template('superadmin/dashboard.html')

@superadmin_bp.route('/api/dashboard/stats')
def api_dashboard_stats():
    """Get dashboard statistics"""
    # User statistics
    total_users = User.query.count()
    users_by_role = {
        'superadmin': User.query.filter_by(role='superadmin').count(),
        'admin': User.query.filter_by(role='admin').count(),
        'organization_admin': User.query.filter_by(role='organization_admin').count(),
        'department_head': User.query.filter_by(role='department_head').count(),
        'professional': User.query.filter_by(role='professional').count(),
        'client': User.query.filter_by(role='client').count(),
        'employee': User.query.filter_by(role='employee').count()
    }
    
    # Pending verifications
    pending_professionals = Professional.query.filter_by(is_verified=False).count()
    
    # Active users (last 30 days)
    active_users = User.query.filter(
        User.last_active >= datetime.utcnow() - timedelta(days=30)
    ).count()
    
    # Session statistics
    total_sessions = Session.query.count()
    sessions_today = Session.query.filter(
        Session.scheduled_date == datetime.now().date()
    ).count()
    
    # Organizations
    total_organizations = Organization.query.count()
    
    # Recent activity
    recent_activity = ActivityLog.query.order_by(
        ActivityLog.created_at.desc()
    ).limit(20).all()
    
    return jsonify({
        'stats': {
            'total_users': total_users,
            'users_by_role': users_by_role,
            'active_users': active_users,
            'pending_professionals': pending_professionals,
            'total_sessions': total_sessions,
            'sessions_today': sessions_today,
            'total_organizations': total_organizations
        },
        'recent_activity': [{
            'id': log.id,
            'user': log.user.get_full_name() if log.user else 'System',
            'action': log.action,
            'description': log.description,
            'time': log.created_at.isoformat(),
            'impersonated': log.impersonated_by is not None
        } for log in recent_activity]
    })

@superadmin_bp.route('/api/users')
def api_get_users():
    """Get all users with filtering"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    role = request.args.get('role', '')
    search = request.args.get('search', '')
    verified = request.args.get('verified', '')
    
    query = User.query
    
    if role:
        query = query.filter_by(role=role)
    
    if search:
        query = query.filter(
            db.or_(
                User.email.ilike(f'%{search}%'),
                User.first_name.ilike(f'%{search}%'),
                User.last_name.ilike(f'%{search}%'),
                User.username.ilike(f'%{search}%')
            )
        )
    
    if verified == 'true':
        query = query.filter_by(is_verified=True)
    elif verified == 'false':
        query = query.filter_by(is_verified=False)
    
    paginated = query.order_by(User.created_at.desc()).paginate(page=page, per_page=per_page)
    
    return jsonify({
        'users': [{
            'id': u.id,
            'username': u.username,
            'email': u.email,
            'first_name': u.first_name,
            'last_name': u.last_name,
            'full_name': u.get_full_name(),
            'role': u.role,
            'is_active': u.is_active,
            'is_verified': u.is_verified,
            'email_verified': u.email_verified,
            'created_at': u.created_at.isoformat() if u.created_at else None,
            'last_login': u.last_login.isoformat() if u.last_login else None,
            'last_active': u.last_active.isoformat() if u.last_active else None
        } for u in paginated.items],
        'total': paginated.total,
        'pages': paginated.pages,
        'current_page': page
    })

@superadmin_bp.route('/api/users/<int:user_id>')
def api_get_user(user_id):
    """Get detailed user information"""
    user = User.query.get_or_404(user_id)
    
    # Get user's activity log
    activity = ActivityLog.query.filter_by(user_id=user.id).order_by(
        ActivityLog.created_at.desc()
    ).limit(50).all()
    
    # Get user's sessions
    sessions = []
    if user.role == 'client' and user.client_profile:
        sessions = Session.query.filter_by(client_id=user.client_profile.id).all()
    elif user.role == 'professional' and user.professional_profile:
        sessions = Session.query.filter_by(professional_id=user.professional_profile.id).all()
    
    return jsonify({
        'user': {
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'phone': user.phone,
            'role': user.role,
            'is_active': user.is_active,
            'is_verified': user.is_verified,
            'email_verified': user.email_verified,
            'created_at': user.created_at.isoformat(),
            'last_login': user.last_login.isoformat() if user.last_login else None,
            'last_active': user.last_active.isoformat() if user.last_active else None,
            'impersonated_by': user.impersonated_by
        },
        'activity': [{
            'action': a.action,
            'description': a.description,
            'ip': a.ip_address,
            'time': a.created_at.isoformat()
        } for a in activity],
        'sessions': [{
            'id': s.id,
            'date': s.scheduled_date.isoformat(),
            'time': s.scheduled_time,
            'status': s.status
        } for s in sessions]
    })

@superadmin_bp.route('/api/users/<int:user_id>/update-role', methods=['POST'])
def api_update_user_role(user_id):
    """Update user role (can promote to admin)"""
    data = request.json
    new_role = data.get('role')
    
    valid_roles = ['client', 'employee', 'professional', 'department_head', 'organization_admin', 'admin', 'superadmin']
    if new_role not in valid_roles:
        return jsonify({'success': False, 'message': 'Invalid role'}), 400
    
    user = User.query.get_or_404(user_id)
    old_role = user.role
    user.role = new_role
    
    # Log the change
    log = ActivityLog(
        user_id=current_user.id,
        action='ROLE_CHANGE',
        description=f'Changed user {user.email} role from {old_role} to {new_role}',
        entity_type='user',
        entity_id=user.id
    )
    db.session.add(log)
    db.session.commit()
    
    # Notify user
    notification = Notification(
        user_id=user.id,
        title='Account Role Updated',
        message=f'Your account role has been updated to {new_role.replace("_", " ").title()}',
        notification_type='info'
    )
    db.session.add(notification)
    db.session.commit()
    
    return jsonify({'success': True, 'message': 'User role updated successfully'})

@superadmin_bp.route('/api/users/<int:user_id>/toggle-status', methods=['POST'])
def api_toggle_user_status(user_id):
    """Activate or deactivate user"""
    user = User.query.get_or_404(user_id)
    user.is_active = not user.is_active
    
    action = 'activated' if user.is_active else 'deactivated'
    
    log = ActivityLog(
        user_id=current_user.id,
        action=f'USER_{action.upper()}',
        description=f'User {user.email} {action}',
        entity_type='user',
        entity_id=user.id
    )
    db.session.add(log)
    
    # Notify user
    notification = Notification(
        user_id=user.id,
        title='Account Status Updated',
        message=f'Your account has been {action}.',
        notification_type='info' if user.is_active else 'warning'
    )
    db.session.add(notification)
    db.session.commit()
    
    return jsonify({
        'success': True,
        'is_active': user.is_active,
        'message': f'User {action} successfully'
    })

@superadmin_bp.route('/api/users/<int:user_id>/reset-password', methods=['POST'])
def api_reset_user_password(user_id):
    """Reset user's password"""
    data = request.json
    new_password = data.get('password')
    
    if not new_password or len(new_password) < 8:
        return jsonify({'success': False, 'message': 'Password must be at least 8 characters'}), 400
    
    user = User.query.get_or_404(user_id)
    user.set_password(new_password)
    
    log = ActivityLog(
        user_id=current_user.id,
        action='PASSWORD_RESET',
        description=f'Password reset for user {user.email}',
        entity_type='user',
        entity_id=user.id
    )
    db.session.add(log)
    
    # Notify user
    notification = Notification(
        user_id=user.id,
        title='Password Reset',
        message='Your password has been reset by an administrator.',
        notification_type='warning'
    )
    db.session.add(notification)
    db.session.commit()
    
    return jsonify({'success': True, 'message': 'Password reset successfully'})

@superadmin_bp.route('/api/users/<int:user_id>/impersonate', methods=['POST'])
def api_impersonate_user(user_id):
    """Impersonate another user (superadmin only)"""
    user = User.query.get_or_404(user_id)
    
    # Store original user in session
    session['impersonator_id'] = current_user.id
    session['original_role'] = current_user.role
    
    # Mark user as being impersonated
    user.impersonated_by = current_user.id
    
    # Log the impersonation
    log = ActivityLog(
        user_id=current_user.id,
        action='IMPERSONATE',
        description=f'Impersonating user {user.email}',
        entity_type='user',
        entity_id=user.id,
        impersonated_by=current_user.id
    )
    db.session.add(log)
    db.session.commit()
    
    # Login as the user
    login_user(user)
    
    return jsonify({
        'success': True,
        'message': f'Now impersonating {user.get_full_name()}',
        'redirect': url_for('dashboard_redirect')
    })

@superadmin_bp.route('/api/stop-impersonating', methods=['POST'])
@login_required
def api_stop_impersonating():
    """Stop impersonating and return to original account"""
    impersonator_id = session.get('impersonator_id')
    
    if not impersonator_id:
        return jsonify({'success': False, 'message': 'Not impersonating'}), 400
    
    # Clear impersonation marker
    current_user.impersonated_by = None
    db.session.commit()
    
    # Log the action
    log = ActivityLog(
        user_id=impersonator_id,
        action='STOP_IMPERSONATE',
        description=f'Stopped impersonating {current_user.email}',
        entity_type='user',
        entity_id=current_user.id
    )
    db.session.add(log)
    db.session.commit()
    
    # Login back as impersonator
    impersonator = User.query.get(impersonator_id)
    login_user(impersonator)
    
    session.pop('impersonator_id', None)
    session.pop('original_role', None)
    
    return jsonify({
        'success': True,
        'message': 'Returned to original account',
        'redirect': url_for('superadmin.dashboard')
    })

@superadmin_bp.route('/api/professionals/pending')
def api_pending_professionals():
    """Get pending professional verifications"""
    professionals = Professional.query.filter_by(is_verified=False).all()
    
    return jsonify([{
        'id': p.id,
        'user_id': p.user_id,
        'name': p.user.get_full_name(),
        'email': p.user.email,
        'professional_type': p.professional_type,
        'license_number': p.license_number,
        'years_experience': p.years_experience,
        'session_fee': p.session_fee,
        'documents': json.loads(p.documents) if p.documents else [],
        'created_at': p.created_at.isoformat() if p.created_at else None
    } for p in professionals])

@superadmin_bp.route('/api/professionals/<int:professional_id>/verify', methods=['POST'])
def api_verify_professional(professional_id):
    """Verify a professional"""
    data = request.json
    notes = data.get('notes', '')
    
    professional = Professional.query.get_or_404(professional_id)
    professional.is_verified = True
    professional.verified_by = current_user.id
    professional.verified_at = datetime.utcnow()
    professional.verification_notes = notes
    
    # Update user verification status
    user = User.query.get(professional.user_id)
    user.is_verified = True
    
    # Notify professional
    notification = Notification(
        user_id=professional.user_id,
        title='Account Verified! 🎉',
        message='Your professional account has been verified. You can now start offering services.',
        notification_type='success',
        link='/professional/dashboard'
    )
    db.session.add(notification)
    
    # Log the verification
    log = ActivityLog(
        user_id=current_user.id,
        action='VERIFY_PROFESSIONAL',
        description=f'Verified professional {user.email}',
        entity_type='professional',
        entity_id=professional.id
    )
    db.session.add(log)
    
    db.session.commit()
    
    return jsonify({'success': True, 'message': 'Professional verified successfully'})

@superadmin_bp.route('/api/professionals/<int:professional_id>/reject', methods=['POST'])
def api_reject_professional(professional_id):
    """Reject a professional verification"""
    data = request.json
    reason = data.get('reason', 'Your application was not approved at this time.')
    
    professional = Professional.query.get_or_404(professional_id)
    
    # Notify professional
    notification = Notification(
        user_id=professional.user_id,
        title='Verification Update',
        message=f'Your professional verification was not approved. Reason: {reason}',
        notification_type='warning',
        link='/professional/profile'
    )
    db.session.add(notification)
    
    # Log the rejection
    log = ActivityLog(
        user_id=current_user.id,
        action='REJECT_PROFESSIONAL',
        description=f'Rejected professional {professional.user.email}: {reason}',
        entity_type='professional',
        entity_id=professional.id
    )
    db.session.add(log)
    
    db.session.commit()
    
    return jsonify({'success': True, 'message': 'Professional rejected'})

@superadmin_bp.route('/api/session-requests/pending')
def api_pending_session_requests():
    """Get pending session requests that need matching"""
    requests = SessionRequest.query.filter_by(
        status='pending'
    ).order_by(SessionRequest.created_at.asc()).all()
    
    return jsonify([{
        'id': r.id,
        'client_id': r.client_id,
        'issue': r.issue_description[:200] + '...' if len(r.issue_description) > 200 else r.issue_description,
        'preferred_date': r.preferred_date.isoformat() if r.preferred_date else None,
        'preferred_time': r.preferred_time,
        'session_type': r.session_type,
        'created_at': r.created_at.isoformat(),
        'expires_at': r.expires_at.isoformat()
    } for r in requests])

@superadmin_bp.route('/api/session-requests/<int:request_id>/match', methods=['POST'])
def api_match_session_request(request_id):
    """Manually match a session request to a professional"""
    data = request.json
    professional_id = data.get('professional_id')
    
    session_request = SessionRequest.query.get_or_404(request_id)
    professional = Professional.query.get_or_404(professional_id)
    
    # Check if professional is verified
    if not professional.is_verified:
        return jsonify({'success': False, 'message': 'Professional is not verified'}), 400
    
    # Update request
    session_request.professional_id = professional.id
    session_request.matched_professional_id = professional.id
    session_request.status = 'matched'
    session_request.matched_at = datetime.utcnow()
    session_request.matched_by = current_user.id
    session_request.is_auto_matched = False
    
    # Notify professional
    notification = Notification(
        user_id=professional.user_id,
        title='New Session Match',
        message=f'You have been matched with a client by an administrator.',
        notification_type='info',
        link='/professional/sessions'
    )
    db.session.add(notification)
    
    # Log the match
    log = ActivityLog(
        user_id=current_user.id,
        action='MANUAL_MATCH',
        description=f'Manually matched session request #{request_id} to professional {professional.user.email}',
        entity_type='session_request',
        entity_id=request_id
    )
    db.session.add(log)
    
    db.session.commit()
    
    return jsonify({'success': True, 'message': 'Session matched successfully'})

@superadmin_bp.route('/api/professionals/available')
def api_available_professionals():
    """Get available professionals for matching"""
    professionals = Professional.query.filter_by(
        is_verified=True,
        is_available=True,
        accepting_clients=True
    ).all()
    
    return jsonify([{
        'id': p.id,
        'name': p.user.get_full_name(),
        'type': p.professional_type,
        'specializations': p.get_specializations(),
        'rating': p.average_rating,
        'session_fee': p.session_fee,
        'current_clients': p.current_clients,
        'max_clients': p.max_clients
    } for p in professionals])

@superadmin_bp.route('/api/site-settings', methods=['GET', 'POST'])
def api_site_settings():
    """Get or update site settings"""
    if request.method == 'GET':
        # Get current settings (you'd store these in a Settings model)
        settings = {
            'site_name': 'Elmed Wellmind Solutions',
            'maintenance_mode': False,
            'registration_open': True,
            'professional_verification_required': True,
            'auto_match_enabled': True,
            'session_timeout_minutes': 10,
            'max_session_duration': 120,
            'min_session_fee': 500,
            'max_session_fee': 20000,
            'platform_fee_percentage': 20,
            'contact_email': 'support@elmedwellmind.com',
            'contact_phone': '+254759226354'
        }
        return jsonify(settings)
    
    else:  # POST
        data = request.json
        # Here you would save settings to database
        # For now, just log and return success
        
        log = ActivityLog(
            user_id=current_user.id,
            action='UPDATE_SETTINGS',
            description='Updated site settings',
            entity_type='settings'
        )
        db.session.add(log)
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Settings updated successfully'})

@superadmin_bp.route('/api/activity-logs')
def api_activity_logs():
    """Get all activity logs"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 50, type=int)
    user_id = request.args.get('user_id', type=int)
    
    query = ActivityLog.query
    
    if user_id:
        query = query.filter_by(user_id=user_id)
    
    logs = query.order_by(ActivityLog.created_at.desc()).paginate(page=page, per_page=per_page)
    
    return jsonify({
        'logs': [{
            'id': log.id,
            'user': log.user.get_full_name() if log.user else 'System',
            'user_email': log.user.email if log.user else None,
            'action': log.action,
            'description': log.description,
            'entity_type': log.entity_type,
            'entity_id': log.entity_id,
            'ip_address': log.ip_address,
            'impersonated': log.impersonated_by is not None,
            'created_at': log.created_at.isoformat()
        } for log in logs.items],
        'total': logs.total,
        'pages': logs.pages,
        'current_page': page
    })

@superadmin_bp.route('/api/analytics')
def api_analytics():
    """Get detailed analytics"""
    # Date ranges
    end_date = datetime.now()
    start_date = end_date - timedelta(days=30)
    
    # User growth
    new_users = db.session.query(
        db.func.date(User.created_at).label('date'),
        db.func.count().label('count')
    ).filter(
        User.created_at >= start_date
    ).group_by(
        db.func.date(User.created_at)
    ).all()
    
    # Session volume
    sessions = db.session.query(
        db.func.date(Session.scheduled_date).label('date'),
        db.func.count().label('count')
    ).filter(
        Session.scheduled_date >= start_date.date()
    ).group_by(
        db.func.date(Session.scheduled_date)
    ).all()
    
    # Revenue
    revenue = db.session.query(
        db.func.date(Session.completed_at).label('date'),
        db.func.sum(Session.total_fee).label('total')
    ).filter(
        Session.completed_at >= start_date,
        Session.status == 'completed'
    ).group_by(
        db.func.date(Session.completed_at)
    ).all()
    
    # Professional performance
    top_professionals = Professional.query.order_by(
        Professional.average_rating.desc()
    ).limit(10).all()
    
    # Organization activity
    active_orgs = Organization.query.order_by(
        Organization.total_sessions.desc()
    ).limit(10).all()
    
    return jsonify({
        'user_growth': [{'date': str(d.date), 'count': d.count} for d in new_users],
        'session_volume': [{'date': str(s.date), 'count': s.count} for s in sessions],
        'revenue': [{'date': str(r.date), 'amount': float(r.total)} for r in revenue if r.total],
        'top_professionals': [{
            'name': p.user.get_full_name(),
            'type': p.professional_type,
            'rating': p.average_rating,
            'sessions': p.total_sessions
        } for p in top_professionals],
        'active_organizations': [{
            'name': o.company_name,
            'employees': o.total_employees,
            'sessions': o.total_sessions,
            'avg_wellness': o.average_wellness_score
        } for o in active_orgs],
        'total_revenue': db.session.query(db.func.sum(Session.total_fee)).filter_by(status='completed').scalar() or 0,
        'avg_session_fee': db.session.query(db.func.avg(Session.total_fee)).filter_by(status='completed').scalar() or 0,
        'completion_rate': (Session.query.filter_by(status='completed').count() / Session.query.count() * 100) if Session.query.count() > 0 else 0
    })