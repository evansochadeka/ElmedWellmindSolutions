# professional_routes.py - Add these endpoints

@professional_bp.route('/api/session-requests')
@login_required
def api_session_requests():
    """Get pending session requests for this professional"""
    professional = current_user.professional_profile
    
    requests = SessionRequest.query.filter_by(
        professional_id=professional.id,
        status='pending'
    ).order_by(SessionRequest.created_at.asc()).all()
    
    return jsonify([{
        'id': r.id,
        'issue': r.issue_description[:100] + '...',
        'preferred_date': r.preferred_date.isoformat() if r.preferred_date else None,
        'preferred_time': r.preferred_time,
        'session_type': r.session_type,
        'expires_at': r.expires_at.isoformat(),
        'created_at': r.created_at.isoformat()
    } for r in requests])

@professional_bp.route('/api/session-requests/<int:request_id>/accept', methods=['POST'])
@login_required
def api_accept_request(request_id):
    """Accept a session request"""
    professional = current_user.professional_profile
    session_request = SessionRequest.query.get_or_404(request_id)
    
    if session_request.professional_id != professional.id:
        return jsonify({'success': False, 'message': 'Unauthorized'}), 403
    
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
    
    session_request.status = 'confirmed'
    db.session.add(session)
    
    # Notify client
    notification = Notification(
        user_id=session_request.client.user_id,
        title='Session Confirmed',
        message=f'Your session has been confirmed by {professional.user.get_full_name()}',
        notification_type='success',
        link='/client/sessions'
    )
    db.session.add(notification)
    db.session.commit()
    
    return jsonify({'success': True})

@professional_bp.route('/api/session-requests/<int:request_id>/decline', methods=['POST'])
@login_required
def api_decline_request(request_id):
    """Decline a session request"""
    professional = current_user.professional_profile
    session_request = SessionRequest.query.get_or_404(request_id)
    
    if session_request.professional_id != professional.id:
        return jsonify({'success': False, 'message': 'Unauthorized'}), 403
    
    session_request.status = 'declined'
    
    # Notify client
    notification = Notification(
        user_id=session_request.client.user_id,
        title='Session Declined',
        message=f'Your session request was declined. Other professionals are available.',
        notification_type='info',
        link='/client/professionals'
    )
    db.session.add(notification)
    db.session.commit()
    
    return jsonify({'success': True})

@professional_bp.route('/api/session-requests/<int:request_id>/postpone', methods=['POST'])
@login_required
def api_postpone_request(request_id):
    """Request to postpone a session"""
    data = request.json
    professional = current_user.professional_profile
    session_request = SessionRequest.query.get_or_404(request_id)
    
    if session_request.professional_id != professional.id:
        return jsonify({'success': False, 'message': 'Unauthorized'}), 403
    
    # Create postponement request
    # You'll need a PostponementRequest model for this
    postponement = PostponementRequest(
        session_request_id=request_id,
        new_date=datetime.strptime(data['date'], '%Y-%m-%d').date(),
        new_time=data['time'],
        reason=data.get('reason', ''),
        status='pending'
    )
    db.session.add(postponement)
    db.session.commit()
    
    return jsonify({'success': True})

@professional_bp.route('/api/sessions')
@login_required
def api_sessions():
    """Get professional's sessions"""
    professional = current_user.professional_profile
    
    upcoming = Session.query.filter_by(
        professional_id=professional.id,
        status='scheduled'
    ).filter(
        Session.scheduled_date >= datetime.now().date()
    ).order_by(Session.scheduled_date).all()
    
    past = Session.query.filter_by(
        professional_id=professional.id
    ).filter(
        Session.scheduled_date < datetime.now().date()
    ).order_by(Session.scheduled_date.desc()).all()
    
    return jsonify({
        'upcoming': [{
            'id': s.id,
            'title': s.title,
            'date': s.scheduled_date.isoformat(),
            'time': s.scheduled_time,
            'status': s.status
        } for s in upcoming],
        'past': [{
            'id': s.id,
            'title': s.title,
            'date': s.scheduled_date.isoformat()
        } for s in past]
    })

@professional_bp.route('/api/earnings')
@login_required
def api_earnings():
    """Get earnings data for charts"""
    professional = current_user.professional_profile
    
    # Get last 6 months of earnings
    earnings_data = []
    labels = []
    
    for i in range(5, -1, -1):
        month = datetime.now() - timedelta(days=30*i)
        labels.append(month.strftime('%b'))
        
        # Calculate earnings for that month
        total = db.session.query(db.func.sum(Session.professional_fee)).filter(
            Session.professional_id == professional.id,
            Session.status == 'completed',
            db.extract('month', Session.completed_at) == month.month,
            db.extract('year', Session.completed_at) == month.year
        ).scalar() or 0
        
        earnings_data.append(float(total))
    
    return jsonify({
        'labels': labels,
        'values': earnings_data
    })

@professional_bp.route('/api/webinars')
@login_required
def api_webinars():
    """Get professional's webinars"""
    professional = current_user.professional_profile
    webinars = Webinar.query.filter_by(professional_id=professional.id).all()
    
    return jsonify([{
        'id': w.id,
        'title': w.title,
        'date': w.scheduled_date.isoformat(),
        'time': w.scheduled_time,
        'current_participants': w.current_participants,
        'max_participants': w.max_participants
    } for w in webinars])

@professional_bp.route('/api/webinars/create', methods=['POST'])
@login_required
def api_create_webinar():
    """Create a new webinar"""
    data = request.json
    professional = current_user.professional_profile
    
    webinar = Webinar(
        professional_id=professional.id,
        title=data['title'],
        description=data['description'],
        topic=data['topic'],
        scheduled_date=datetime.strptime(data['date'], '%Y-%m-%d').date(),
        scheduled_time=data['time'],
        duration_minutes=int(data['duration']),
        max_participants=int(data['max_participants']),
        is_free=data.get('is_free', False),
        fee=0 if data.get('is_free') else professional.session_fee * 2
    )
    
    db.session.add(webinar)
    db.session.commit()
    
    return jsonify({'success': True})

@professional_bp.route('/api/messages')
@login_required
def api_messages():
    """Get recent messages"""
    professional = current_user.professional_profile
    
    # Get unique conversations
    sessions = db.session.query(ChatMessage.session_id).filter(
        ChatMessage.user_id == professional.user_id
    ).distinct().all()
    
    messages = []
    for session in sessions[:10]:  # Limit to 10 most recent
        last_msg = ChatMessage.query.filter_by(session_id=session[0])\
                    .order_by(ChatMessage.created_at.desc()).first()
        if last_msg:
            messages.append({
                'content': last_msg.content,
                'timestamp': last_msg.created_at.isoformat(),
                'sent_by_me': last_msg.user_id == professional.user_id,
                'avatar': last_msg.user.profile_pic if last_msg.user else None
            })
    
    return jsonify(messages)

@professional_bp.route('/api/messages/send', methods=['POST'])
@login_required
def api_send_message():
    """Send message to client"""
    data = request.json
    professional = current_user.professional_profile
    
    # Create unique session ID
    session_id = f"{min(professional.user_id, data['client_id'])}_{max(professional.user_id, data['client_id'])}"
    
    message = ChatMessage(
        user_id=professional.user_id,
        session_id=session_id,
        role='professional',
        content=data['message']
    )
    db.session.add(message)
    
    # Notify client
    notification = Notification(
        user_id=data['client_id'],
        title='New Message',
        message=f'Dr. {professional.user.get_full_name()} sent you a message',
        notification_type='info',
        link='/client/messages'
    )
    db.session.add(notification)
    db.session.commit()
    
    return jsonify({'success': True})

@professional_bp.route('/api/disputes')
@login_required
def api_disputes():
    """Get disputes involving this professional"""
    professional = current_user.professional_profile
    
    # You'll need a Dispute model for this
    disputes = Dispute.query.filter_by(professional_id=professional.id).all()
    
    return jsonify([{
        'id': d.id,
        'reason': d.reason,
        'status': d.status
    } for d in disputes])

@professional_bp.route('/api/disputes/<int:dispute_id>/respond', methods=['POST'])
@login_required
def api_respond_dispute(dispute_id):
    """Respond to a dispute"""
    data = request.json
    professional = current_user.professional_profile
    
    dispute = Dispute.query.get_or_404(dispute_id)
    if dispute.professional_id != professional.id:
        return jsonify({'success': False, 'message': 'Unauthorized'}), 403
    
    dispute.professional_response = data['response']
    dispute.proposed_resolution = data['resolution']
    dispute.status = 'responded'
    
    db.session.commit()
    
    return jsonify({'success': True})

@professional_bp.route('/api/calendar-events')
@login_required
def api_calendar_events():
    """Get calendar events for fullcalendar"""
    professional = current_user.professional_profile
    
    sessions = Session.query.filter_by(professional_id=professional.id).all()
    
    events = []
    for session in sessions:
        events.append({
            'title': f'Session with Client',
            'start': f"{session.scheduled_date}T{session.scheduled_time}",
            'description': session.description,
            'color': '#667eea'
        })
    
    webinars = Webinar.query.filter_by(professional_id=professional.id).all()
    for webinar in webinars:
        events.append({
            'title': f'Webinar: {webinar.title}',
            'start': f"{webinar.scheduled_date}T{webinar.scheduled_time}",
            'description': webinar.description,
            'color': '#10B981'
        })
    
    return jsonify(events)

@professional_bp.route('/api/update-profile', methods=['POST'])
@login_required
def api_update_profile():
    """Update professional profile"""
    try:
        user = current_user
        professional = user.professional_profile
        
        # Update user fields
        user.first_name = request.form.get('first_name', user.first_name)
        user.last_name = request.form.get('last_name', user.last_name)
        user.email = request.form.get('email', user.email)
        user.phone = request.form.get('phone', user.phone)
        user.bio = request.form.get('bio', user.bio)
        
        # Update professional fields
        professional.session_fee = float(request.form.get('session_fee', professional.session_fee))
        
        specializations = request.form.get('specializations', '[]')
        try:
            professional.specialization = json.dumps(json.loads(specializations))
        except:
            professional.specialization = json.dumps([s.strip() for s in specializations.split(',') if s.strip()])
        
        # Handle profile photo
        if 'profile_photo' in request.files:
            photo = request.files['profile_photo']
            if photo and photo.filename:
                filename = secure_filename(f"prof_{user.id}_{int(datetime.utcnow().timestamp())}.jpg")
                photo_path = os.path.join('static', 'uploads', 'profiles', filename)
                photo.save(photo_path)
                user.profile_pic = filename
        
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Profile updated successfully'})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500

@professional_bp.route('/api/session-requests/<int:request_id>/expire', methods=['POST'])
@login_required
def api_expire_request(request_id):
    """Mark a request as expired and make it available to other professionals"""
    session_request = SessionRequest.query.get_or_404(request_id)
    
    if session_request.status == 'pending' and session_request.expires_at < datetime.utcnow():
        session_request.status = 'expired'
        
        # Notify other professionals
        professionals = Professional.query.filter_by(is_available=True, is_verified=True).all()
        for prof in professionals:
            if prof.id != session_request.professional_id:
                notification = Notification(
                    user_id=prof.user_id,
                    title='New Session Request Available',
                    message='A client is waiting for a session',
                    notification_type='info',
                    link='/professional/requests'
                )
                db.session.add(notification)
        
        db.session.commit()
        
    return jsonify({'success': True})
