# services/matching_service.py
from models import db, SessionRequest, Professional, Notification, Session, User
from datetime import datetime, timedelta
from flask import current_app
import threading
import time
import random

class MatchingService:
    """Service to automatically match clients with professionals"""
    
    @staticmethod
    def find_best_match(session_request):
        """Find the best professional match for a session request"""
        
        # Get all available and verified professionals
        professionals = Professional.query.filter_by(
            is_available=True,
            accepting_clients=True,
            is_verified=True
        ).all()
        
        if not professionals:
            return None
        
        # Score each professional based on various factors
        scored_professionals = []
        for prof in professionals:
            score = 0
            
            # Check availability for requested time
            if session_request.preferred_date and session_request.preferred_time:
                if MatchingService.check_availability(prof, session_request.preferred_date, session_request.preferred_time):
                    score += 30
            
            # Check specialization match (simple keyword matching)
            if session_request.issue_description:
                specializations = prof.get_specializations()
                issue_lower = session_request.issue_description.lower()
                for spec in specializations:
                    if spec.lower() in issue_lower:
                        score += 20
                        break
            
            # Response rate and rating
            score += (prof.response_rate or 0) * 0.2
            score += (prof.average_rating or 0) * 5
            
            # Experience
            score += (prof.years_experience or 0) * 2
            
            # Lower session count gets priority (load balancing)
            score += max(0, 50 - (prof.total_sessions or 0))
            
            scored_professionals.append((prof, score))
        
        # Sort by score and return best match
        scored_professionals.sort(key=lambda x: x[1], reverse=True)
        
        if scored_professionals:
            # Add some randomness to avoid always picking the same professional
            top_performers = scored_professionals[:3]
            return random.choice(top_performers)[0] if len(top_performers) > 1 else scored_professionals[0][0]
        
        return None
    
    @staticmethod
    def check_availability(professional, date, time):
        """Check if professional is available at given date and time"""
        # This would check against their availability schedule
        # For now, return True for simplicity
        # In production, you'd check ProfessionalAvailability table
        return True
    
    @staticmethod
    def auto_match_requests():
        """Background task to auto-match pending requests"""
        while True:
            try:
                # Find pending requests that need matching
                pending_requests = SessionRequest.query.filter_by(
                    status='pending'
                ).filter(
                    SessionRequest.expires_at > datetime.utcnow()
                ).all()
                
                for request in pending_requests:
                    # Find best match
                    best_match = MatchingService.find_best_match(request)
                    
                    if best_match:
                        # Assign to professional
                        request.matched_professional_id = best_match.id
                        request.is_auto_matched = True
                        request.status = 'matched'
                        request.matched_at = datetime.utcnow()
                        request.professional_id = best_match.id
                        
                        # Create notification for professional
                        notification = Notification(
                            user_id=best_match.user_id,
                            title='New Session Match',
                            message=f'You have been matched with a client. You have 10 minutes to confirm.',
                            notification_type='info',
                            link='/professional/sessions'
                        )
                        db.session.add(notification)
                        
                        db.session.commit()
                        
                        # Start timer for confirmation
                        timer = threading.Timer(600, MatchingService.check_confirmation, args=[request.id])
                        timer.daemon = True
                        timer.start()
                        
                        print(f"✅ Matched request #{request.id} to professional #{best_match.id}")
                    
                    else:
                        # No match found, notify admin after 5 minutes
                        if not request.admin_notified and request.created_at < datetime.utcnow() - timedelta(minutes=5):
                            MatchingService.notify_admin(request, "No matching professional found")
                            request.admin_notified = True
                            db.session.commit()
                
                time.sleep(30)  # Check every 30 seconds
                
            except Exception as e:
                current_app.logger.error(f"Auto-match error: {str(e)}")
                time.sleep(60)
    
    @staticmethod
    def check_confirmation(request_id):
        """Check if professional confirmed the match within 10 minutes"""
        from flask import current_app
        
        with current_app.app_context():
            try:
                request = SessionRequest.query.get(request_id)
                if request and request.status == 'matched':
                    # Professional didn't confirm, make it available for others
                    request.status = 'pending'
                    request.matched_professional_id = None
                    request.is_auto_matched = False
                    request.professional_id = None
                    
                    # Notify admin
                    MatchingService.notify_admin(request, f"Professional didn't confirm match for request #{request_id}")
                    
                    # Notify all professionals
                    professionals = Professional.query.filter_by(is_available=True, is_verified=True).all()
                    for prof in professionals:
                        notification = Notification(
                            user_id=prof.user_id,
                            title='New Session Request Available',
                            message='A client is waiting for a session. Check your dashboard.',
                            notification_type='info',
                            link='/professional/dashboard'
                        )
                        db.session.add(notification)
                    
                    db.session.commit()
                    print(f"⚠️ Request #{request_id} expired - professional didn't confirm")
                    
            except Exception as e:
                current_app.logger.error(f"Error in check_confirmation: {str(e)}")
    
    @staticmethod
    def notify_admin(request, message=None):
        """Notify admin about unmatched or expired request"""
        from models import User
        
        try:
            admins = User.query.filter_by(role='admin').all()
            for admin in admins:
                notification = Notification(
                    user_id=admin.id,
                    title='⚠️ Session Request Needs Attention',
                    message=message or f'Request #{request.id} needs attention',
                    notification_type='warning',
                    link='/admin/session-requests'
                )
                db.session.add(notification)
            db.session.commit()
            print(f"📢 Notified admins about request #{request.id}")
        except Exception as e:
            current_app.logger.error(f"Error notifying admin: {str(e)}")

# Start the matching service in a background thread
def start_matching_service(app):
    """Start the matching service in a background thread"""
    def run_matching():
        with app.app_context():
            print("🚀 Starting matching service...")
            MatchingService.auto_match_requests()
    
    # Only start if not in debug mode or if explicitly enabled
    if not app.debug or os.environ.get('ENABLE_MATCHING_IN_DEBUG', 'false').lower() == 'true':
        thread = threading.Thread(target=run_matching, daemon=True)
        thread.start()
        print("✅ Matching service started in background thread")
    else:
        print("ℹ️ Matching service not started (debug mode)")