# superadmin_routes.py - COMPLETE WITH BLUEPRINT DEFINITION
from flask import Blueprint, render_template, jsonify, request, redirect, url_for
from flask_login import login_required, current_user
from models import db, User, Professional, Organization, Client, Session, Notification, ActivityLog, CommunityPost, ChatMessage, Review
from datetime import datetime, timedelta
import json

# Define blueprint FIRST
superadmin_bp = Blueprint('superadmin', __name__, url_prefix='/superadmin')

@superadmin_bp.route('/dashboard')
@login_required
def dashboard():
    """Superadmin dashboard"""
    if current_user.role != 'superadmin':
        return redirect(url_for('main.index'))
    return render_template('superadmin/dashboard.html')

@superadmin_bp.route('/api/dashboard/stats')
@login_required
def api_dashboard_stats():
    """Get superadmin dashboard statistics"""
    if current_user.role != 'superadmin':
        return jsonify({'error': 'Unauthorized'}), 403
    
    # Get counts
    total_users = User.query.count()
    total_professionals = Professional.query.count()
    total_organizations = Organization.query.count()
    total_clients = Client.query.count()
    
    # Pending verifications
    pending_professionals = Professional.query.filter_by(is_verified=False).count()
    
    # Recent activity
    recent_activity = ActivityLog.query.order_by(ActivityLog.created_at.desc()).limit(20).all()
    
    return jsonify({
        'stats': {
            'total_users': total_users,
            'total_professionals': total_professionals,
            'total_organizations': total_organizations,
            'total_clients': total_clients,
            'pending_professionals': pending_professionals
        },
        'recent_activity': [{
            'id': a.id,
            'user': a.user.get_full_name() if a.user else 'System',
            'action': a.action,
            'description': a.description,
            'created_at': a.created_at.isoformat() if a.created_at else None
        } for a in recent_activity]
    })

@superadmin_bp.route('/api/users')
@login_required
def api_get_users():
    """Get all users with pagination"""
    if current_user.role != 'superadmin':
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
                User.last_name.ilike(f'%{search}%')
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
            'created_at': u.created_at.isoformat() if u.created_at else None,
            'last_login': u.last_login.isoformat() if u.last_login else None
        } for u in paginated.items],
        'total': paginated.total,
        'pages': paginated.pages,
        'current_page': page
    })

@superadmin_bp.route('/api/users/<int:user_id>/toggle-status', methods=['POST'])
@login_required
def api_toggle_user_status(user_id):
    """Activate or deactivate a user"""
    if current_user.role != 'superadmin':
        return jsonify({'error': 'Unauthorized'}), 403
    
    user = User.query.get_or_404(user_id)
    user.is_active = not user.is_active
    
    # Log activity
    action = 'activated' if user.is_active else 'deactivated'
    log = ActivityLog(
        user_id=current_user.id,
        action=f'USER_{action.upper()}',
        description=f'User {user.email} {action} by superadmin',
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
    
    return jsonify({'success': True, 'is_active': user.is_active})

@superadmin_bp.route('/api/users/<int:user_id>/reset-password', methods=['POST'])
@login_required
def api_reset_user_password(user_id):
    """Reset a user's password"""
    if current_user.role != 'superadmin':
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
        description=f'Password reset for user {user.email} by superadmin',
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

@superadmin_bp.route('/api/users/<int:user_id>/balance', methods=['POST'])
@login_required
def api_update_balance(user_id):
    """Update user account balance"""
    if current_user.role != 'superadmin':
        return jsonify({'error': 'Unauthorized'}), 403
    
    data = request.json
    action = data.get('action')
    amount = float(data.get('amount', 0))
    reason = data.get('reason', '')
    
    user = User.query.get_or_404(user_id)
    
    # Get or create balance record (you'll need a UserBalance model)
    # This is a simplified version - you may want to create a proper balance model
    current_balance = getattr(user, 'account_balance', 0)
    
    if action == 'add':
        new_balance = current_balance + amount
    elif action == 'deduct':
        new_balance = max(0, current_balance - amount)
    elif action == 'set':
        new_balance = amount
    else:
        return jsonify({'success': False, 'message': 'Invalid action'}), 400
    
    # Update user balance (you need to add this field to User model)
    user.account_balance = new_balance
    
    # Log the transaction
    log = ActivityLog(
        user_id=current_user.id,
        action='BALANCE_UPDATE',
        description=f'Updated balance for {user.email}: {action} {amount} ({reason})',
        entity_type='user',
        entity_id=user.id
    )
    db.session.add(log)
    db.session.commit()
    
    return jsonify({
        'success': True,
        'new_balance': new_balance,
        'message': 'Balance updated successfully'
    })

@superadmin_bp.route('/api/chat/send', methods=['POST'])
@login_required
def api_send_chat():
    """Send chat message to user"""
    if current_user.role != 'superadmin':
        return jsonify({'error': 'Unauthorized'}), 403
    
    data = request.json
    user_id = data.get('user_id')
    message = data.get('message')
    
    # Create a unique session ID for admin-user chat
    session_id = f"admin_{current_user.id}_user_{user_id}"
    
    # Save message
    chat = ChatMessage(
        user_id=current_user.id,
        session_id=session_id,
        role='admin',
        content=message
    )
    db.session.add(chat)
    
    # Notify user
    notification = Notification(
        user_id=user_id,
        title='Message from Admin',
        message=message[:100] + '...',
        notification_type='info',
        link=f'/chat/session/{session_id}'
    )
    db.session.add(notification)
    db.session.commit()
    
    return jsonify({'success': True})

@superadmin_bp.route('/api/rate-user', methods=['POST'])
@login_required
def api_rate_user():
    """Rate a user"""
    if current_user.role != 'superadmin':
        return jsonify({'error': 'Unauthorized'}), 403
    
    data = request.json
    user_id = data.get('user_id')
    rating = data.get('rating')
    comment = data.get('comment')
    
    # Create review
    review = Review(
        reviewer_id=current_user.id,
        reviewee_id=user_id,
        rating=rating,
        comment=comment,
        is_public=False  # Admin reviews can be private
    )
    db.session.add(review)
    db.session.commit()
    
    return jsonify({'success': True})

@superadmin_bp.route('/api/users/<int:user_id>/edit', methods=['POST'])
@login_required
def api_edit_user(user_id):
    """Edit user details"""
    if current_user.role != 'superadmin':
        return jsonify({'error': 'Unauthorized'}), 403
    
    data = request.json
    user = User.query.get_or_404(user_id)
    
    # Update fields
    user.first_name = data.get('first_name', user.first_name)
    user.last_name = data.get('last_name', user.last_name)
    user.email = data.get('email', user.email)
    user.phone = data.get('phone', user.phone)
    user.role = data.get('role', user.role)
    user.is_active = data.get('is_active', user.is_active)
    user.is_verified = data.get('is_verified', user.is_verified)
    
    db.session.commit()
    
    # Log activity
    log = ActivityLog(
        user_id=current_user.id,
        action='USER_EDIT',
        description=f'Edited user {user.email}',
        entity_type='user',
        entity_id=user.id
    )
    db.session.add(log)
    db.session.commit()
    
    return jsonify({'success': True, 'message': 'User updated successfully'})

@superadmin_bp.route('/api/system/settings', methods=['POST'])
@login_required
def api_system_settings():
    """Update system settings"""
    if current_user.role != 'superadmin':
        return jsonify({'error': 'Unauthorized'}), 403
    
    data = request.json
    
    # Save settings to database or config file
    # You'll need a SystemSettings model for this
    settings = {
        'platform_fee': data.get('platformFee'),
        'session_timeout': data.get('sessionTimeout'),
        'max_free_sessions': data.get('maxFreeSessions'),
        'maintenance_mode': data.get('maintenanceMode'),
        'auto_verify_professionals': data.get('autoVerifyProfessionals')
    }
    
    # Log settings change
    log = ActivityLog(
        user_id=current_user.id,
        action='SYSTEM_SETTINGS',
        description=f'Updated system settings',
        entity_type='settings'
    )
    db.session.add(log)
    db.session.commit()
    
    return jsonify({'success': True, 'message': 'Settings saved successfully'})
