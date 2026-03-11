# admin_routes.py - Complete Admin Routes
from flask import Blueprint, render_template, jsonify, request, redirect, url_for
from flask_login import login_required, current_user
from models import db, User, Professional, Organization, Client, Session, Notification, ActivityLog, CommunityPost, ChatMessage
from datetime import datetime, timedelta
import json

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

@admin_bp.route('/dashboard')
@login_required
def dashboard():
    """Admin dashboard page"""
    if current_user.role != 'admin':
        return redirect(url_for('main.index'))
    return render_template('admin/dashboard.html')

@admin_bp.route('/api/dashboard/stats')
@login_required
def api_dashboard_stats():
    """Get admin dashboard statistics"""
    if current_user.role != 'admin':
        return jsonify({'error': 'Unauthorized'}), 403
    
    # Get counts
    total_users = User.query.count()
    total_clients = User.query.filter_by(role='client').count()
    total_professionals = User.query.filter_by(role='professional').count()
    total_organizations = User.query.filter_by(role='organization').count()
    total_admins = User.query.filter_by(role='admin').count()
    
    # Pending verifications
    pending_professionals = Professional.query.filter_by(is_verified=False).count()
    pending_organizations = Organization.query.filter(Organization.is_verified==False).count() if hasattr(Organization, 'is_verified') else 0
    
    # Recent activity
    recent_users = User.query.order_by(User.created_at.desc()).limit(10).all()
    
    # Sessions today
    sessions_today = Session.query.filter(
        Session.scheduled_date == datetime.now().date()
    ).count()
    
    # Community posts today
    posts_today = CommunityPost.query.filter(
        db.func.date(CommunityPost.created_at) == datetime.now().date()
    ).count()
    
    # Chat messages today
    chats_today = ChatMessage.query.filter(
        db.func.date(ChatMessage.created_at) == datetime.now().date()
    ).count()
    
    return jsonify({
        'stats': {
            'total_users': total_users,
            'total_clients': total_clients,
            'total_professionals': total_professionals,
            'total_organizations': total_organizations,
            'total_admins': total_admins,
            'pending_professionals': pending_professionals,
            'pending_organizations': pending_organizations,
            'sessions_today': sessions_today,
            'posts_today': posts_today,
            'chats_today': chats_today
        },
        'recent_users': [{
            'id': u.id,
            'name': u.get_full_name(),
            'email': u.email,
            'role': u.role,
            'created_at': u.created_at.isoformat() if u.created_at else None,
            'is_active': u.is_active,
            'is_verified': u.is_verified
        } for u in recent_users]
    })

@admin_bp.route('/api/professionals/pending')
@login_required
def api_pending_professionals():
    """Get pending professional verifications"""
    if current_user.role != 'admin':
        return jsonify({'error': 'Unauthorized'}), 403
    
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

@admin_bp.route('/api/professionals/verify/<int:professional_id>', methods=['POST'])
@login_required
def api_verify_professional(professional_id):
    """Verify a professional"""
    if current_user.role != 'admin':
        return jsonify({'error': 'Unauthorized'}), 403
    
    professional = Professional.query.get_or_404(professional_id)
    professional.is_verified = True
    professional.verified_by = current_user.id
    professional.verified_at = datetime.utcnow()
    
    # Update user verification status
    user = User.query.get(professional.user_id)
    if user:
        user.is_verified = True
    
    # Notify professional
    notification = Notification(
        user_id=professional.user_id,
        title='Account Verified',
        message='Your professional account has been verified. You can now start offering services.',
        notification_type='success',
        link='/professional/dashboard'
    )
    db.session.add(notification)
    
    db.session.commit()
    
    return jsonify({'success': True, 'message': 'Professional verified successfully'})

@admin_bp.route('/api/professionals/reject/<int:professional_id>', methods=['POST'])
@login_required
def api_reject_professional(professional_id):
    """Reject a professional verification"""
    if current_user.role != 'admin':
        return jsonify({'error': 'Unauthorized'}), 403
    
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
    
    # Optionally delete or mark as rejected
    professional.is_verified = False
    
    db.session.commit()
    
    return jsonify({'success': True, 'message': 'Professional rejected'})

@admin_bp.route('/api/users')
@login_required
def api_get_users():
    """Get all users with pagination"""
    if current_user.role != 'admin':
        return jsonify({'error': 'Unauthorized'}), 403
    
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    role = request.args.get('role', '')
    search = request.args.get('search', '')
    
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
            'last_login': u.last_login.isoformat() if u.last_login else None
        } for u in paginated.items],
        'total': paginated.total,
        'pages': paginated.pages,
        'current_page': page
    })

@admin_bp.route('/api/users/<int:user_id>', methods=['GET'])
@login_required
def api_get_user(user_id):
    """Get detailed user information"""
    if current_user.role != 'admin':
        return jsonify({'error': 'Unauthorized'}), 403
    
    user = User.query.get_or_404(user_id)
    
    result = {
        'id': user.id,
        'username': user.username,
        'email': user.email,
        'first_name': user.first_name,
        'last_name': user.last_name,
        'phone': user.phone,
        'role': user.role,
        'bio': user.bio,
        'profile_pic': user.profile_pic,
        'is_active': user.is_active,
        'is_verified': user.is_verified,
        'email_verified': user.email_verified,
        'phone_verified': user.phone_verified,
        'created_at': user.created_at.isoformat() if user.created_at else None,
        'updated_at': user.updated_at.isoformat() if user.updated_at else None,
        'last_login': user.last_login.isoformat() if user.last_login else None
    }
    
    # Add role-specific data
    if user.role == 'professional' and user.professional_profile:
        prof = user.professional_profile
        result['professional'] = {
            'id': prof.id,
            'professional_type': prof.professional_type,
            'license_number': prof.license_number,
            'years_experience': prof.years_experience,
            'specialization': prof.get_specializations(),
            'session_fee': prof.session_fee,
            'is_verified': prof.is_verified,
            'verified_by': prof.verified_by,
            'verified_at': prof.verified_at.isoformat() if prof.verified_at else None,
            'documents': json.loads(prof.documents) if prof.documents else [],
            'total_sessions': prof.total_sessions,
            'average_rating': prof.average_rating
        }
    
    elif user.role == 'organization' and user.organization_profile:
        org = user.organization_profile
        result['organization'] = {
            'id': org.id,
            'company_name': org.company_name,
            'registration_number': org.registration_number,
            'industry': org.industry,
            'company_size': org.company_size,
            'employee_registration_code': org.employee_registration_code,
            'total_employees': org.total_employees,
            'active_this_month': org.active_this_month,
            'total_sessions': org.total_sessions,
            'average_wellness_score': org.average_wellness_score,
            'high_risk_employees': org.high_risk_employees
        }
    
    elif user.role == 'client' and user.client_profile:
        client = user.client_profile
        result['client'] = {
            'id': client.id,
            'brief_issue': client.brief_issue,
            'emergency_contact': client.emergency_contact,
            'emergency_contact_name': client.emergency_contact_name,
            'organization_id': client.organization_id,
            'department': client.department,
            'employee_id': client.employee_id,
            'wellness_score': client.wellness_score,
            'risk_level': client.risk_level
        }
    
    return jsonify(result)

@admin_bp.route('/api/users/<int:user_id>/toggle-status', methods=['POST'])
@login_required
def api_toggle_user_status(user_id):
    """Activate or deactivate a user"""
    if current_user.role != 'admin':
        return jsonify({'error': 'Unauthorized'}), 403
    
    user = User.query.get_or_404(user_id)
    user.is_active = not user.is_active
    
    # Log activity
    action = 'activated' if user.is_active else 'deactivated'
    log = ActivityLog(
        user_id=current_user.id,
        action=f'USER_{action.upper()}',
        description=f'User {user.email} {action} by admin',
        entity_type='user',
        entity_id=user.id,
        ip_address=request.remote_addr
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

@admin_bp.route('/api/users/<int:user_id>/reset-password', methods=['POST'])
@login_required
def api_reset_user_password(user_id):
    """Reset a user's password"""
    if current_user.role != 'admin':
        return jsonify({'error': 'Unauthorized'}), 403
    
    data = request.json
    new_password = data.get('password')
    
    if not new_password or len(new_password) < 8:
        return jsonify({'success': False, 'message': 'Password must be at least 8 characters'}), 400
    
    user = User.query.get_or_404(user_id)
    user.set_password(new_password)
    
    # Log activity
    log = ActivityLog(
        user_id=current_user.id,
        action='PASSWORD_RESET',
        description=f'Password reset for user {user.email} by admin',
        entity_type='user',
        entity_id=user.id,
        ip_address=request.remote_addr
    )
    db.session.add(log)
    
    # Notify user
    notification = Notification(
        user_id=user.id,
        title='Password Reset',
        message='Your password has been reset by an administrator.',
        notification_type='info'
    )
    db.session.add(notification)
    
    db.session.commit()
    
    return jsonify({'success': True, 'message': 'Password reset successfully'})

@admin_bp.route('/api/users/<int:user_id>/edit', methods=['POST'])
@login_required
def api_edit_user(user_id):
    """Edit user details"""
    if current_user.role != 'admin':
        return jsonify({'error': 'Unauthorized'}), 403
    
    data = request.json
    user = User.query.get_or_404(user_id)
    
    # Update basic fields
    if 'first_name' in data:
        user.first_name = data['first_name']
    if 'last_name' in data:
        user.last_name = data['last_name']
    if 'email' in data:
        user.email = data['email']
    if 'phone' in data:
        user.phone = data['phone']
    if 'role' in data and data['role'] in ['client', 'professional', 'organization', 'admin']:
        user.role = data['role']
    if 'is_verified' in data:
        user.is_verified = data['is_verified']
    
    db.session.commit()
    
    # Log activity
    log = ActivityLog(
        user_id=current_user.id,
        action='USER_EDITED',
        description=f'User {user.email} details updated by admin',
        entity_type='user',
        entity_id=user.id,
        ip_address=request.remote_addr
    )
    db.session.add(log)
    db.session.commit()
    
    return jsonify({'success': True, 'message': 'User updated successfully'})

@admin_bp.route('/api/activity-logs')
@login_required
def api_activity_logs():
    """Get activity logs"""
    if current_user.role != 'admin':
        return jsonify({'error': 'Unauthorized'}), 403
    
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 50, type=int)
    
    logs = ActivityLog.query.order_by(ActivityLog.created_at.desc())\
           .paginate(page=page, per_page=per_page)
    
    return jsonify({
        'logs': [{
            'id': log.id,
            'user_id': log.user_id,
            'user_email': log.user.email if log.user else 'System',
            'user_name': log.user.get_full_name() if log.user else 'System',
            'action': log.action,
            'description': log.description,
            'entity_type': log.entity_type,
            'entity_id': log.entity_id,
            'ip_address': log.ip_address,
            'created_at': log.created_at.isoformat() if log.created_at else None
        } for log in logs.items],
        'total': logs.total,
        'pages': logs.pages,
        'current_page': page
    })

@admin_bp.route('/api/analytics')
@login_required
def api_analytics():
    """Get platform analytics"""
    if current_user.role != 'admin':
        return jsonify({'error': 'Unauthorized'}), 403
    
    # Last 30 days
    end_date = datetime.now()
    start_date = end_date - timedelta(days=30)
    
    # New users by day
    new_users = db.session.query(
        db.func.date(User.created_at).label('date'),
        db.func.count().label('count')
    ).filter(
        User.created_at >= start_date
    ).group_by(
        db.func.date(User.created_at)
    ).all()
    
    # Sessions by day
    sessions = db.session.query(
        db.func.date(Session.scheduled_date).label('date'),
        db.func.count().label('count')
    ).filter(
        Session.scheduled_date >= start_date.date()
    ).group_by(
        db.func.date(Session.scheduled_date)
    ).all()
    
    # Revenue by day
    revenue = db.session.query(
        db.func.date(Session.completed_at).label('date'),
        db.func.sum(Session.total_fee).label('total')
    ).filter(
        Session.completed_at >= start_date,
        Session.status == 'completed'
    ).group_by(
        db.func.date(Session.completed_at)
    ).all()
    
    # User roles distribution
    roles_distribution = db.session.query(
        User.role,
        db.func.count().label('count')
    ).group_by(User.role).all()
    
    return jsonify({
        'new_users': [{'date': str(d.date), 'count': d.count} for d in new_users],
        'sessions': [{'date': str(s.date), 'count': s.count} for s in sessions],
        'revenue': [{'date': str(r.date), 'total': float(r.total)} for r in revenue if r.total],
        'roles': [{'role': r.role, 'count': r.count} for r in roles_distribution],
        'total_revenue': db.session.query(db.func.sum(Session.total_fee)).filter_by(status='completed').scalar() or 0
    })

@admin_bp.route('/api/notifications')
@login_required
def api_get_notifications():
    """Get admin notifications"""
    if current_user.role != 'admin':
        return jsonify({'error': 'Unauthorized'}), 403
    
    notifications = Notification.query.filter_by(
        user_id=current_user.id,
        is_read=False
    ).order_by(Notification.created_at.desc()).all()
    
    return jsonify([{
        'id': n.id,
        'title': n.title,
        'message': n.message,
        'type': n.notification_type,
        'link': n.link,
        'created_at': n.created_at.isoformat() if n.created_at else None
    } for n in notifications])

@admin_bp.route('/api/notifications/mark-read', methods=['POST'])
@login_required
def api_mark_notifications_read():
    """Mark all notifications as read"""
    if current_user.role != 'admin':
        return jsonify({'error': 'Unauthorized'}), 403
    
    Notification.query.filter_by(user_id=current_user.id, is_read=False)\
        .update({Notification.is_read: True, Notification.read_at: datetime.utcnow()})
    db.session.commit()
    
    return jsonify({'success': True})

@admin_bp.route('/api/community/posts/moderate')
@login_required
def api_get_pending_posts():
    """Get posts pending moderation"""
    if current_user.role != 'admin':
        return jsonify({'error': 'Unauthorized'}), 403
    
    posts = CommunityPost.query.filter_by(is_approved=False).order_by(CommunityPost.created_at.desc()).all()
    
    return jsonify([post.to_dict() for post in posts])

@admin_bp.route('/api/community/posts/<int:post_id>/approve', methods=['POST'])
@login_required
def api_approve_post(post_id):
    """Approve a community post"""
    if current_user.role != 'admin':
        return jsonify({'error': 'Unauthorized'}), 403
    
    post = CommunityPost.query.get_or_404(post_id)
    post.is_approved = True
    
    db.session.commit()
    
    return jsonify({'success': True, 'message': 'Post approved'})

@admin_bp.route('/api/community/posts/<int:post_id>/delete', methods=['DELETE'])
@login_required
def api_delete_post(post_id):
    """Delete a community post"""
    if current_user.role != 'admin':
        return jsonify({'error': 'Unauthorized'}), 403
    
    post = CommunityPost.query.get_or_404(post_id)
    db.session.delete(post)
    db.session.commit()
    
    return jsonify({'success': True, 'message': 'Post deleted'})
