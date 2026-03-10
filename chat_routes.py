# chat_routes.py
from flask import Blueprint, render_template, jsonify, request, redirect, url_for
from flask_login import login_required, current_user
from models import db, ChatMessage, User, Professional, Client, Notification
from datetime import datetime

chat_bp = Blueprint('chat', __name__, url_prefix='/chat')

@chat_bp.route('/professionals')
@login_required
def professionals_list():
    """List all verified professionals"""
    professionals = Professional.query.filter_by(is_verified=True).all()
    return render_template('chat/professionals.html', professionals=professionals)

@chat_bp.route('/api/professionals')
@login_required
def api_professionals():
    """API endpoint to get all verified professionals"""
    professionals = Professional.query.filter_by(is_verified=True).all()
    
    return jsonify([{
        'id': p.id,
        'user_id': p.user_id,
        'name': p.user.get_full_name(),
        'profile_pic': p.user.profile_pic,
        'professional_type': p.professional_type,
        'specializations': p.get_specializations(),
        'years_experience': p.years_experience,
        'session_fee': p.session_fee,
        'average_rating': p.average_rating,
        'bio': p.user.bio,
        'is_available': p.is_available
    } for p in professionals])

@chat_bp.route('/professional/<int:professional_id>')
@login_required
def professional_profile(professional_id):
    """View professional profile"""
    professional = Professional.query.get_or_404(professional_id)
    return render_template('chat/professional_profile.html', professional=professional)

@chat_bp.route('/conversation/<int:professional_id>')
@login_required
def conversation(professional_id):
    """Start or continue conversation with professional"""
    professional = Professional.query.get_or_404(professional_id)
    
    # Get or create a unique session ID for this conversation
    session_id = f"{min(current_user.id, professional.user_id)}_{max(current_user.id, professional.user_id)}"
    
    return render_template('chat/conversation.html', 
                         professional=professional,
                         session_id=session_id)

@chat_bp.route('/api/messages/<session_id>')
@login_required
def get_messages(session_id):
    """Get all messages for a session"""
    messages = ChatMessage.query.filter_by(session_id=session_id)\
                .order_by(ChatMessage.created_at.asc())\
                .all()
    
    return jsonify([{
        'id': m.id,
        'user_id': m.user_id,
        'sender_name': m.user.get_full_name() if m.user else 'Unknown',
        'sender_role': m.user.role if m.user else 'unknown',
        'content': m.content,
        'timestamp': m.created_at.isoformat()
    } for m in messages])

@chat_bp.route('/api/send', methods=['POST'])
@login_required
def send_message():
    """Send a message"""
    data = request.json
    session_id = data.get('session_id')
    content = data.get('content')
    receiver_id = data.get('receiver_id')
    
    if not content or not session_id:
        return jsonify({'success': False, 'message': 'Message content required'}), 400
    
    # Create message
    message = ChatMessage(
        user_id=current_user.id,
        session_id=session_id,
        role='user',
        content=content
    )
    db.session.add(message)
    
    # Create notification for receiver
    if receiver_id:
        notification = Notification(
            user_id=receiver_id,
            title='New Message',
            message=f'{current_user.get_full_name()} sent you a message',
            notification_type='info',
            link=f'/chat/conversation/{current_user.id if current_user.role == "professional" else data.get("professional_id")}'
        )
        db.session.add(notification)
    
    db.session.commit()
    
    return jsonify({
        'success': True,
        'message': {
            'id': message.id,
            'content': message.content,
            'timestamp': message.created_at.isoformat()
        }
    })

@chat_bp.route('/api/mark-read/<session_id>', methods=['POST'])
@login_required
def mark_messages_read(session_id):
    """Mark all messages in a session as read"""
    messages = ChatMessage.query.filter_by(session_id=session_id)\
                .filter(ChatMessage.user_id != current_user.id)\
                .all()
    
    # You could add an 'is_read' field to ChatMessage model if needed
    # For now, just return success
    
    return jsonify({'success': True})

@chat_bp.route('/api/professionals/search')
@login_required
def search_professionals():
    """Search professionals by name, type, or specialization"""
    query = request.args.get('q', '')
    
    if not query:
        return jsonify([])
    
    professionals = Professional.query.filter_by(is_verified=True).all()
    
    results = []
    query_lower = query.lower()
    
    for p in professionals:
        # Search in name
        if query_lower in p.user.get_full_name().lower():
            results.append(p)
            continue
        
        # Search in professional type
        if query_lower in p.professional_type.lower():
            results.append(p)
            continue
        
        # Search in specializations
        specializations = p.get_specializations()
        for spec in specializations:
            if query_lower in spec.lower():
                results.append(p)
                break
    
    return jsonify([{
        'id': p.id,
        'name': p.user.get_full_name(),
        'profile_pic': p.user.profile_pic,
        'type': p.professional_type,
        'specializations': p.get_specializations(),
        'rating': p.average_rating
    } for p in results[:10]])