# superadmin_routes.py - Add these endpoints

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