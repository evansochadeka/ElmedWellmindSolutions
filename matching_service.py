# services/matching_service.py
from models import db, SessionRequest, Professional, Notification, Session
from datetime import datetime, timedelta
from flask import current_app
import threading
import time

class MatchingService:
    @staticmethod
    def find_best_match(session_request):
        """Find the best professional match for a session request"""
        
        # Get all available professionals
        professionals = Professional.query.filter_by(
            is_available=True,
            accepting_clients=True,
            is_verified=True
        ).all()
        
        if not professionals:
            return None
        
        # Score each professional
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
                for spec in specializations:
                    if spec.lower() in session_request.issue_description.lower():
                        score += 20
                        break
            
            # Response rate and rating
            score += prof.response_rate * 0.2
            score += prof.average_rating * 5
            
            # Experience
            score += prof.years_experience * 2
            
            scored_professionals.append((prof, score))
        
        # Sort by score and return best match
        scored_professionals.sort(key=lambda x: x[1], reverse=True)
        
        if scored_professionals:
            return scored_professionals[0][0]
        
        return None
    
    @staticmethod
    def check_availability(professional, date, time):
        """Check if professional is available at given date and time"""
        # This would check against their availability schedule
        # For now, return True for simplicity
        return True
    
    @staticmethod
    def auto_match_requests():
        """Background task to auto-match pending requests"""
        while True:
            try:
                # Find pending requests that need matching
                pending_requests = SessionRequest.query.filter_by(
                    status='pending',
                    is_auto_matched=False
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
                        threading.Timer(600, MatchingService.check_confirmation, args=[request.id]).start()
                    
                    else:
                        # No match found, notify admin after 5 minutes
                        if not request.admin_notified and request.created_at < datetime.utcnow() - timedelta(minutes=5):
                            MatchingService.notify_admin(request)
                            request.admin_notified = True
                            db.session.commit()
                
                time.sleep(30)  # Check every 30 seconds
                
            except Exception as e:
                current_app.logger.error(f"Auto-match error: {str(e)}")
                time.sleep(60)
    
    @staticmethod
    def check_confirmation(request_id):
        """Check if professional confirmed the match within 10 minutes"""
        with current_app.app_context():
            request = SessionRequest.query.get(request_id)
            if request and request.status == 'matched':
                # Professional didn't confirm, make it available for others
                request.status = 'pending'
                request.matched_professional_id = None
                request.is_auto_matched = False
                
                # Notify admin
                MatchingService.notify_admin(request, f"Professional didn't confirm match for request #{request_id}")
                
                # Notify all professionals
                professionals = Professional.query.filter_by(is_available=True).all()
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
    
    @staticmethod
    def notify_admin(request, message=None):
        """Notify admin about unmatched or expired request"""
        from models import User
        
        admins = User.query.filter_by(role='admin').all()
        for admin in admins:
            notification = Notification(
                user_id=admin.id,
                title='Session Request Attention Needed',
                message=message or f'Request #{request.id} needs attention',
                notification_type='warning',
                link='/admin/session-requests'
            )
            db.session.add(notification)
        db.session.commit()

# Start the matching service in a background thread
def start_matching_service(app):
    with app.app_context():
        thread = threading.Thread(target=MatchingService.auto_match_requests, daemon=True)
        thread.start()