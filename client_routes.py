# client_routes.py - Add these endpoints

@client_bp.route('/api/dashboard/data')
@login_required
def api_dashboard_data():
    """Get client dashboard data"""
    client = Client.query.filter_by(user_id=current_user.id).first()
    if not client:
        return jsonify({'error': 'Client profile not found'}), 404
    
    # Get wellness data
    assessments = WellnessAssessment.query.filter_by(client_id=client.id)\
                    .order_by(WellnessAssessment.created_at.desc()).all()
    
    # Calculate streak (simplified)
    streak = calculate_streak(client)
    
    return jsonify({
        'employee': {
            'wellness_score': client.wellness_score,
            'risk_level': client.risk_level
        },
        'services_accessed': {
            'counseling': Session.query.filter_by(client_id=client.id).count()
        },
        'streak': streak,
        'progress_data': [a.overall_score for a in assessments[-30:]]
    })

@client_bp.route('/api/professionals')
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
        'session_fee': p.client_facing_fee,
        'average_rating': p.average_rating,
        'bio': p.user.bio,
        'total_sessions': p.total_sessions,
        'response_rate': p.response_rate
    } for p in professionals])

@client_bp.route('/api/professionals/<int:professional_id>')
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
        'session_fee': professional.client_facing_fee,
        'average_rating': professional.average_rating,
        'bio': professional.user.bio,
        'total_sessions': professional.total_sessions,
        'response_rate': professional.response_rate,
        'reviews': [{
            'reviewer_name': r.reviewer.get_full_name(),
            'rating': r.rating,
            'comment': r.comment,
            'created_at': r.created_at.isoformat()
        } for r in reviews],
        'availability': []  # Add availability data
    })

@client_bp.route('/api/chat/history/<int:professional_id>')
@login_required
def api_chat_history(professional_id):
    """Get chat history with a professional"""
    professional = Professional.query.get_or_404(professional_id)
    
    # Create unique session ID for this conversation
    session_id = f"{min(current_user.id, professional.user_id)}_{max(current_user.id, professional.user_id)}"
    
    messages = ChatMessage.query.filter_by(session_id=session_id)\
                .order_by(ChatMessage.created_at.asc()).all()
    
    return jsonify([{
        'content': m.content,
        'timestamp': m.created_at.isoformat(),
        'sent_by_me': m.user_id == current_user.id,
        'avatar': m.user.profile_pic if m.user else None
    } for m in messages])

@client_bp.route('/api/chat/send', methods=['POST'])
@login_required
def api_send_chat():
    """Send message to professional"""
    data = request.json
    professional_id = data.get('professional_id')
    message = data.get('message')
    
    professional = Professional.query.get_or_404(professional_id)
    
    # Create unique session ID
    session_id = f"{min(current_user.id, professional.user_id)}_{max(current_user.id, professional.user_id)}"
    
    chat = ChatMessage(
        user_id=current_user.id,
        session_id=session_id,
        role='user',
        content=message
    )
    db.session.add(chat)
    
    # Create notification for professional
    notification = Notification(
        user_id=professional.user_id,
        title='New Message',
        message=f'{current_user.get_full_name()} sent you a message',
        notification_type='info',
        link=f'/professional/chat/{current_user.id}'
    )
    db.session.add(notification)
    db.session.commit()
    
    return jsonify({'success': True})

@client_bp.route('/api/rate-professional', methods=['POST'])
@login_required
def api_rate_professional():
    """Rate a professional after session"""
    data = request.json
    professional_id = data.get('professional_id')
    rating = data.get('rating')
    comment = data.get('comment')
    
    professional = Professional.query.get_or_404(professional_id)
    
    review = Review(
        session_id=None,  # Optional: link to specific session
        reviewer_id=current_user.id,
        reviewee_id=professional.user_id,
        rating=rating,
        comment=comment,
        is_public=True
    )
    db.session.add(review)
    
    # Update professional's average rating
    all_ratings = Review.query.filter_by(reviewee_id=professional.user_id).all()
    professional.average_rating = sum(r.rating for r in all_ratings) / len(all_ratings)
    
    db.session.commit()
    
    return jsonify({'success': True})

@client_bp.route('/api/sessions')
@login_required
def api_sessions():
    """Get client's sessions"""
    client = Client.query.filter_by(user_id=current_user.id).first()
    
    upcoming = Session.query.filter_by(client_id=client.id, status='scheduled')\
                .filter(Session.scheduled_date >= datetime.now().date())\
                .order_by(Session.scheduled_date).all()
    
    past = Session.query.filter_by(client_id=client.id)\
            .filter(Session.scheduled_date < datetime.now().date())\
            .order_by(Session.scheduled_date.desc()).all()
    
    return jsonify({
        'upcoming': [{
            'id': s.id,
            'title': s.title,
            'date': s.scheduled_date.isoformat(),
            'time': s.scheduled_time,
            'professional_name': s.professional.user.get_full_name(),
            'status': s.status
        } for s in upcoming],
        'past': [{
            'id': s.id,
            'title': s.title,
            'date': s.scheduled_date.isoformat(),
            'professional_name': s.professional.user.get_full_name(),
            'rating': s.review.rating if s.review else None
        } for s in past]
    })

@client_bp.route('/api/assessments')
@login_required
def api_assessments():
    """Get client's assessment history and recommendations"""
    client = Client.query.filter_by(user_id=current_user.id).first()
    
    assessments = WellnessAssessment.query.filter_by(client_id=client.id)\
                    .order_by(WellnessAssessment.created_at.desc()).all()
    
    # Get latest recommendations
    latest = assessments[0] if assessments else None
    recommendations = json.loads(latest.recommendations) if latest and latest.recommendations else []
    
    return jsonify({
        'assessments': [{
            'id': a.id,
            'date': a.created_at.isoformat(),
            'score': a.overall_score,
            'risk_level': a.risk_level
        } for a in assessments],
        'recommendations': recommendations
    })

@client_bp.route('/api/update-profile', methods=['POST'])
@login_required
def api_update_profile():
    """Update client profile"""
    try:
        user = current_user
        
        # Update text fields
        user.first_name = request.form.get('first_name', user.first_name)
        user.last_name = request.form.get('last_name', user.last_name)
        user.email = request.form.get('email', user.email)
        user.phone = request.form.get('phone', user.phone)
        user.bio = request.form.get('bio', user.bio)
        
        if request.form.get('date_of_birth'):
            user.date_of_birth = datetime.strptime(request.form.get('date_of_birth'), '%Y-%m-%d').date()
        
        user.gender = request.form.get('gender', user.gender)
        
        # Handle profile photo upload
        if 'profile_photo' in request.files:
            photo = request.files['profile_photo']
            if photo and photo.filename:
                filename = secure_filename(f"client_{user.id}_{int(datetime.utcnow().timestamp())}.jpg")
                photo_path = os.path.join('static', 'uploads', 'profiles', filename)
                photo.save(photo_path)
                user.profile_pic = filename
        
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Profile updated successfully'})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500

def calculate_streak(client):
    """Calculate user's activity streak"""
    # Simplified - you can implement based on last_active
    return 7  # Placeholder