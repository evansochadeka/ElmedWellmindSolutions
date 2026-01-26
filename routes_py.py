# routes_py.py - UPDATED WITH WORKING MODELS
from flask import Blueprint, request, jsonify, current_app
from models import ChatMessage, CommunityPost, PostComment, db
import os
import requests
import uuid
from datetime import datetime
import random

api = Blueprint('api', __name__, url_prefix='/api')

# Fallback responses for when AI is unavailable
FALLBACK_RESPONSES = [
    "I understand you're reaching out. For personalized support, please contact our counselors at +254759226354.",
    "Thank you for sharing. Our team is available 24/7 via WhatsApp at +254759226354 for mental health support.",
    "I appreciate you reaching out. Remember, professional help is available. Call +254759226354 to speak with someone.",
    "Your mental health matters. For immediate support, contact our helpline at +254759226354.",
    "Thank you for trusting me with this. For more personalized help, our counselors are available at +254759226354.",
    "I hear you. It takes courage to reach out. For ongoing support, our team at +254759226354 is here for you.",
    "I understand. Mental health challenges can be difficult. Remember, help is available at +254759226354.",
    "Thank you for sharing your feelings. For professional guidance, please contact our team at +254759226354."
]

# Available Cohere models (try in this order)
COHERE_MODELS = [
    'command-r-08-2024',      # Latest Command R
    'command-r-plus-08-2024', # Latest Command R Plus
    'command-r',              # General Command R
    'command-r-plus',         # General Command R Plus
    'aya-23-8B',              # Aya 8B model
    'aya-23-35B',             # Aya 35B model
    'c4ai-command-r-v01',     # C4AI model
    'c4ai-command-r-plus',    # C4AI plus model
]

# System prompt for mental health assistant
SYSTEM_PROMPT = """You are 'Elmed Wellmind Solutions', a compassionate mental health assistant specifically designed for Kenyan users. Your role is to provide supportive, empathetic responses with general mental health information and evidence-based coping strategies.

CRITICAL RULES:
1. NEVER provide medical diagnoses, prescriptions, or specific treatment plans
2. ALWAYS encourage seeking professional help for serious or persistent issues
3. If someone expresses suicidal thoughts, immediately direct them to emergency services: Call +254759226354 or 999
4. Be culturally sensitive to Kenyan context - consider economic, social, and family factors
5. Use simple, clear language accessible to most Kenyans
6. Focus on psychoeducation, emotional validation, and practical coping skills
7. When appropriate, mention culturally relevant resources (community support, faith-based resources if mentioned)
8. Validate feelings and normalize mental health challenges

RESPONSE STYLE:
- Start with empathy: "I hear you..." or "Thank you for sharing..."
- Provide 1-2 practical, culturally appropriate suggestions
- End with encouragement to seek professional help if needed
- Mention our contact: Elmed Wellmind Solutions at +254759226354
- If unsure, say: "I recommend speaking with a mental health professional about this"

Remember: You are not a substitute for professional mental healthcare. Your role is to provide supportive information and guide users toward appropriate resources."""

def get_intelligent_fallback(message):
    """Return context-aware fallback response based on message content"""
    message_lower = message.lower()
    
    # Emergency/suicidal thoughts
    if any(word in message_lower for word in ['suicide', 'kill myself', 'end my life', 'want to die', 'harm myself']):
        return "🚨 EMERGENCY: Please call our emergency line immediately at +254759226354 or dial 999. You are not alone, and help is available right now. We care about you."
    
    # Anxiety
    elif any(word in message_lower for word in ['anxious', 'anxiety', 'panic', 'worried', 'nervous', 'overthinking']):
        return "I understand you're feeling anxious. Try this breathing exercise: Inhale for 4 seconds, hold for 4, exhale for 6. Repeat 5 times. For ongoing anxiety support, contact our counselors at +254759226354."
    
    # Depression
    elif any(word in message_lower for word in ['depressed', 'sad', 'hopeless', 'unmotivated', 'empty', 'worthless']):
        return "I hear you're feeling down. Depression is treatable, and you don't have to go through this alone. Please reach out to our team at +254759226354 for professional support."
    
    # Stress
    elif any(word in message_lower for word in ['stress', 'overwhelmed', 'pressure', 'burnout', 'stressed']):
        return "Stress can feel overwhelming. Try breaking tasks into smaller, manageable steps. For personalized stress management techniques, call our team at +254759226354."
    
    # Sleep issues
    elif any(word in message_lower for word in ['sleep', 'insomnia', 'tired', 'exhausted', 'can\'t sleep']):
        return "Sleep issues can significantly affect mental health. Try establishing a consistent bedtime routine and avoiding screens before bed. For sleep counseling, contact +254759226354."
    
    # Relationships
    elif any(word in message_lower for word in ['relationship', 'partner', 'breakup', 'divorce', 'family', 'friend']):
        return "Relationship challenges can be difficult. Remember that healthy communication is key. For relationship counseling, our team at +254759226354 can help."
    
    # Work/school stress
    elif any(word in message_lower for word in ['work', 'job', 'school', 'exam', 'study', 'deadline']):
        return "Work/school pressure can be challenging. Try prioritizing tasks and taking regular breaks. For career or academic counseling, call +254759226354."
    
    # General fallback
    else:
        return random.choice(FALLBACK_RESPONSES)

def call_cohere_api(api_key, message, chat_history):
    """Try to call Cohere API with different models"""
    for model in COHERE_MODELS:
        try:
            response = requests.post(
                'https://api.cohere.com/v1/chat',
                headers={
                    'Authorization': f'Bearer {api_key}',
                    'Content-Type': 'application/json',
                    'Accept': 'application/json'
                },
                json={
                    'model': model,
                    'message': message,
                    'chat_history': chat_history,
                    'preamble': SYSTEM_PROMPT,
                    'temperature': 0.7,
                    'max_tokens': 800,
                    'prompt_truncation': 'AUTO'
                },
                timeout=15
            )
            
            if response.status_code == 200:
                result = response.json()
                bot_response = result.get('text', '').strip()
                if bot_response:
                    current_app.logger.info(f"✅ Successfully used Cohere model: {model}")
                    return bot_response
            
        except requests.exceptions.RequestException as e:
            current_app.logger.debug(f"Model {model} failed: {e}")
            continue
        except Exception as e:
            current_app.logger.debug(f"Error with model {model}: {e}")
            continue
    
    return None

# AI CHAT ROUTE
@api.route('/chat', methods=['POST'])
def chat():
    try:
        data = request.json
        message = data.get('message', '').strip()
        session_id = data.get('session_id', str(uuid.uuid4()))
        
        if not message:
            return jsonify({'error': 'Message cannot be empty'}), 400
        
        # Save user message to database
        user_message = ChatMessage(
            session_id=session_id,
            role='user',
            content=message,
            is_mental_health_related=True
        )
        db.session.add(user_message)
        db.session.commit()
        
        # Get Cohere API key
        cohere_key = os.environ.get('COHERE_API_KEY')
        
        # Prepare chat history
        chat_history = []
        if cohere_key:
            try:
                # Get recent chat history for context
                recent_messages = ChatMessage.query.filter_by(session_id=session_id)\
                    .order_by(ChatMessage.created_at.desc())\
                    .limit(6)\
                    .all()
                
                # Format history for Cohere (most recent first, then reverse for context)
                history_for_api = []
                for msg in reversed(recent_messages):
                    if msg.role == 'user':
                        history_for_api.append({"role": "USER", "message": msg.content})
                    elif msg.role == 'assistant':
                        history_for_api.append({"role": "CHATBOT", "message": msg.content})
                
                # Try to call Cohere API
                bot_response = call_cohere_api(cohere_key, message, history_for_api)
                
                if bot_response:
                    # Ensure response includes emergency contact for serious concerns
                    serious_keywords = ['suicide', 'kill myself', 'end my life', 'want to die', 'harm myself', 'emergency', 'urgent']
                    if any(keyword in message.lower() for keyword in serious_keywords):
                        if '+254759226354' not in bot_response and '999' not in bot_response:
                            bot_response += "\n\n🚨 EMERGENCY: If you're having thoughts of harming yourself, please call our emergency line immediately: +254759226354 or dial 999."
                else:
                    # Cohere API failed, use intelligent fallback
                    bot_response = get_intelligent_fallback(message)
                    current_app.logger.info("⚠️ Using intelligent fallback response")
                    
            except Exception as e:
                current_app.logger.error(f"Cohere API attempt failed: {e}")
                bot_response = get_intelligent_fallback(message)
                current_app.logger.info("⚠️ Using fallback after API error")
        else:
            # No API key, use intelligent fallback
            bot_response = get_intelligent_fallback(message)
            current_app.logger.info("⚠️ No API key, using intelligent fallback")
        
        # Save assistant response to database
        assistant_message = ChatMessage(
            session_id=session_id,
            role='assistant',
            content=bot_response,
            is_mental_health_related=True
        )
        db.session.add(assistant_message)
        db.session.commit()
        
        return jsonify({
            'response': bot_response,
            'session_id': session_id,
            'timestamp': datetime.utcnow().isoformat(),
            'source': 'cohere' if cohere_key and 'fallback' not in bot_response.lower() else 'fallback'
        })
        
    except Exception as e:
        current_app.logger.error(f"Unexpected error in chat endpoint: {e}")
        fallback = random.choice(FALLBACK_RESPONSES)
        return jsonify({
            'response': fallback,
            'session_id': session_id if 'session_id' in locals() else str(uuid.uuid4()),
            'timestamp': datetime.utcnow().isoformat(),
            'source': 'error_fallback'
        })

# Get chat history for a session
@api.route('/chat/history/<session_id>', methods=['GET'])
def get_chat_history(session_id):
    try:
        messages = ChatMessage.query.filter_by(session_id=session_id)\
                     .order_by(ChatMessage.created_at.asc())\
                     .limit(100)\
                     .all()
        
        return jsonify([{
            'id': m.id,
            'role': m.role,
            'content': m.content,
            'timestamp': m.created_at.isoformat() if m.created_at else None,
            'is_mental_health_related': m.is_mental_health_related
        } for m in messages])
    except Exception as e:
        current_app.logger.error(f"Error getting chat history: {e}")
        return jsonify([])

# ... rest of your routes remain the same ...