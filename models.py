# models.py - Complete System Models (FULLY CORRECTED)
from extensions import db
from datetime import datetime, timedelta
from sqlalchemy.orm import relationship
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
import uuid
import json
import secrets

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    first_name = db.Column(db.String(100), nullable=False)
    last_name = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20), nullable=True)
    
    # Role-based access
    role = db.Column(db.String(50), default='client')  # client, professional, organization, admin
    
    # Profile
    profile_pic = db.Column(db.String(200), default='default.jpg')
    bio = db.Column(db.Text, nullable=True)
    date_of_birth = db.Column(db.Date, nullable=True)
    gender = db.Column(db.String(20), nullable=True)
    
    # Account status
    is_active = db.Column(db.Boolean, default=True)
    is_verified = db.Column(db.Boolean, default=False)
    email_verified = db.Column(db.Boolean, default=False)
    phone_verified = db.Column(db.Boolean, default=False)
    two_factor_enabled = db.Column(db.Boolean, default=False)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login = db.Column(db.DateTime, nullable=True)
    last_active = db.Column(db.DateTime, nullable=True)
    
    # Relationships
    client_profile = db.relationship('Client', back_populates='user', uselist=False, cascade='all, delete-orphan')
    professional_profile = db.relationship('Professional', back_populates='user', uselist=False, cascade='all, delete-orphan')
    organization_profile = db.relationship('Organization', back_populates='user', uselist=False, cascade='all, delete-orphan')
    notifications = db.relationship('Notification', back_populates='user', cascade='all, delete-orphan')
    reviews_given = db.relationship('Review', foreign_keys='Review.reviewer_id', back_populates='reviewer')
    reviews_received = db.relationship('Review', foreign_keys='Review.reviewee_id', back_populates='reviewee')
    
    # Chat messages relationship
    chat_messages = db.relationship('ChatMessage', back_populates='user', cascade='all, delete-orphan')
    
    # Security tokens
    reset_token = db.Column(db.String(100), nullable=True)
    reset_token_expiry = db.Column(db.DateTime, nullable=True)
    verification_token = db.Column(db.String(100), nullable=True)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def generate_reset_token(self):
        self.reset_token = secrets.token_urlsafe(32)
        self.reset_token_expiry = datetime.utcnow() + timedelta(hours=24)
        return self.reset_token
    
    def verify_reset_token(self, token):
        return self.reset_token == token and self.reset_token_expiry > datetime.utcnow()
    
    def get_full_name(self):
        return f"{self.first_name} {self.last_name}"
    
    @property
    def is_admin(self):
        return self.role == 'admin'
    
    @property
    def is_professional(self):
        return self.role == 'professional'
    
    @property
    def is_organization(self):
        return self.role == 'organization'
    
    @property
    def is_client(self):
        return self.role == 'client'

class Client(db.Model):
    __tablename__ = 'clients'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, unique=True)
    
    # Client specific fields
    brief_issue = db.Column(db.Text, nullable=True)
    emergency_contact = db.Column(db.String(20), nullable=True)
    emergency_contact_name = db.Column(db.String(100), nullable=True)
    
    # Preferences
    preferred_language = db.Column(db.String(50), default='English')
    preferred_gender = db.Column(db.String(20), nullable=True)
    communication_preference = db.Column(db.String(50), default='video')  # video, chat, phone
    
    # Organization association (if they belong to one)
    organization_id = db.Column(db.Integer, db.ForeignKey('organizations.id'), nullable=True)
    department = db.Column(db.String(100), nullable=True)
    employee_id = db.Column(db.String(100), nullable=True)
    
    # Privacy settings
    hide_profile = db.Column(db.Boolean, default=False)
    allow_contact = db.Column(db.Boolean, default=False)
    
    # Wellness tracking
    wellness_score = db.Column(db.Float, default=0.0)  # Calculated from assessments
    risk_level = db.Column(db.String(20), default='low')  # low, medium, high
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = db.relationship('User', back_populates='client_profile')
    organization = db.relationship('Organization', back_populates='employees')
    sessions = db.relationship('Session', back_populates='client')
    session_requests = db.relationship('SessionRequest', back_populates='client')
    assessments = db.relationship('WellnessAssessment', back_populates='client')
    
    # Community posts relationship
    community_posts = db.relationship('CommunityPost', back_populates='author', cascade='all, delete-orphan')
    post_comments = db.relationship('PostComment', back_populates='author', cascade='all, delete-orphan')

class Professional(db.Model):
    __tablename__ = 'professionals'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, unique=True)
    
    # Professional details
    professional_type = db.Column(db.String(50), nullable=False)  # counselor, psychiatrist, psychologist, therapist
    license_number = db.Column(db.String(100), nullable=False)
    years_experience = db.Column(db.Integer, nullable=True)
    specialization = db.Column(db.Text, nullable=True)  # JSON array of specializations
    
    # Fees
    session_fee = db.Column(db.Float, nullable=False, default=0.0)  # Base fee
    currency = db.Column(db.String(10), default='KES')
    
    # Document verification
    documents = db.Column(db.Text, nullable=True)  # JSON array of document paths
    is_verified = db.Column(db.Boolean, default=False)
    verified_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    verified_at = db.Column(db.DateTime, nullable=True)
    
    # Availability
    available_days = db.Column(db.Text, nullable=True)  # JSON array of available days
    available_hours = db.Column(db.Text, nullable=True)  # JSON of time slots
    
    # Statistics
    total_sessions = db.Column(db.Integer, default=0)
    average_rating = db.Column(db.Float, default=0.0)
    response_rate = db.Column(db.Float, default=0.0)  # Percentage
    response_time = db.Column(db.Integer, default=0)  # Average in minutes
    
    # Status
    is_available = db.Column(db.Boolean, default=True)
    accepting_clients = db.Column(db.Boolean, default=True)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = db.relationship('User', back_populates='professional_profile')
    sessions = db.relationship('Session', back_populates='professional')
    session_requests = db.relationship('SessionRequest', back_populates='professional')
    webinars = db.relationship('Webinar', back_populates='professional')
    availability = db.relationship('ProfessionalAvailability', back_populates='professional')
    
    @property
    def client_facing_fee(self):
        """Fee that clients see (professional fee + 20% platform fee)"""
        return self.session_fee * 1.2
    
    def get_specializations(self):
        if self.specialization:
            return json.loads(self.specialization)
        return []

class Organization(db.Model):
    __tablename__ = 'organizations'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, unique=True)
    
    # Organization details
    company_name = db.Column(db.String(200), nullable=False)
    registration_number = db.Column(db.String(100), nullable=False)
    industry = db.Column(db.String(100), nullable=True)  # FIXED: Removed extra '.db'
    company_size = db.Column(db.Integer, default=0)  # Number of employees
    
    # Registration code for employees
    employee_registration_code = db.Column(db.String(50), unique=True, nullable=True)
    
    # Statistics
    total_employees = db.Column(db.Integer, default=0)
    active_this_month = db.Column(db.Integer, default=0)
    total_sessions = db.Column(db.Integer, default=0)
    average_wellness_score = db.Column(db.Float, default=0.0)
    high_risk_employees = db.Column(db.Integer, default=0)
    
    # Settings
    allow_anonymous_sessions = db.Column(db.Boolean, default=True)
    hide_employee_issues = db.Column(db.Boolean, default=True)  # Don't show specific issues to org
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = db.relationship('User', back_populates='organization_profile')
    employees = db.relationship('Client', back_populates='organization')
    departments = db.relationship('Department', back_populates='organization')
    wellness_data = db.relationship('OrganizationWellnessData', back_populates='organization')
    
    def generate_employee_code(self):
        self.employee_registration_code = secrets.token_hex(4).upper()  # 8 character code
        return self.employee_registration_code

class Department(db.Model):
    __tablename__ = 'departments'
    id = db.Column(db.Integer, primary_key=True)
    organization_id = db.Column(db.Integer, db.ForeignKey('organizations.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    
    # Statistics
    employee_count = db.Column(db.Integer, default=0)
    average_wellness_score = db.Column(db.Float, default=0.0)
    high_risk_count = db.Column(db.Integer, default=0)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    organization = db.relationship('Organization', back_populates='departments')
    employees = db.relationship('Client', foreign_keys='Client.department')

class SessionRequest(db.Model):
    __tablename__ = 'session_requests'
    id = db.Column(db.Integer, primary_key=True)
    client_id = db.Column(db.Integer, db.ForeignKey('clients.id'), nullable=False)
    professional_id = db.Column(db.Integer, db.ForeignKey('professionals.id'), nullable=True)
    
    # Request details
    issue_description = db.Column(db.Text, nullable=False)
    preferred_date = db.Column(db.Date, nullable=True)
    preferred_time = db.Column(db.String(20), nullable=True)
    session_type = db.Column(db.String(50), default='video')  # video, chat, phone
    
    # Matching
    is_auto_matched = db.Column(db.Boolean, default=False)
    matched_professional_id = db.Column(db.Integer, db.ForeignKey('professionals.id'), nullable=True)
    matched_at = db.Column(db.DateTime, nullable=True)
    
    # Status
    status = db.Column(db.String(20), default='pending')  # pending, matched, confirmed, expired, cancelled
    expires_at = db.Column(db.DateTime, default=lambda: datetime.utcnow() + timedelta(minutes=10))
    
    # Notifications
    admin_notified = db.Column(db.Boolean, default=False)
    notification_sent_at = db.Column(db.DateTime, nullable=True)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    client = db.relationship('Client', back_populates='session_requests')
    professional = db.relationship('Professional', foreign_keys=[professional_id])
    matched_professional = db.relationship('Professional', foreign_keys=[matched_professional_id])
    session = db.relationship('Session', back_populates='request', uselist=False)

class Session(db.Model):
    __tablename__ = 'sessions'
    id = db.Column(db.Integer, primary_key=True)
    request_id = db.Column(db.Integer, db.ForeignKey('session_requests.id'), nullable=True)
    client_id = db.Column(db.Integer, db.ForeignKey('clients.id'), nullable=False)
    professional_id = db.Column(db.Integer, db.ForeignKey('professionals.id'), nullable=False)
    
    # Session details
    session_type = db.Column(db.String(50), nullable=False)  # individual, group, webinar
    title = db.Column(db.String(200), nullable=True)
    description = db.Column(db.Text, nullable=True)
    
    # Scheduling
    scheduled_date = db.Column(db.Date, nullable=False)
    scheduled_time = db.Column(db.String(20), nullable=False)
    duration_minutes = db.Column(db.Integer, default=60)
    
    # Fees
    professional_fee = db.Column(db.Float, nullable=False)  # What professional gets
    platform_fee = db.Column(db.Float, nullable=False)  # 20% of professional fee
    total_fee = db.Column(db.Float, nullable=False)  # What client pays
    
    # Meeting details
    meeting_link = db.Column(db.String(500), nullable=True)
    meeting_password = db.Column(db.String(100), nullable=True)
    
    # Status
    status = db.Column(db.String(20), default='scheduled')  # scheduled, ongoing, completed, cancelled, no_show
    cancellation_reason = db.Column(db.Text, nullable=True)
    
    # Anonymity
    is_anonymous = db.Column(db.Boolean, default=False)  # If client requested anonymity
    hide_contact = db.Column(db.Boolean, default=True)  # Don't show professional's contact
    
    # Timestamps
    started_at = db.Column(db.DateTime, nullable=True)
    completed_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    client = db.relationship('Client', back_populates='sessions')
    professional = db.relationship('Professional', back_populates='sessions')
    request = db.relationship('SessionRequest', back_populates='session')
    feedback = db.relationship('SessionFeedback', back_populates='session', uselist=False)
    review = db.relationship('Review', back_populates='session', uselist=False)

class Webinar(db.Model):
    __tablename__ = 'webinars'
    id = db.Column(db.Integer, primary_key=True)
    professional_id = db.Column(db.Integer, db.ForeignKey('professionals.id'), nullable=False)
    
    # Webinar details
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    topic = db.Column(db.String(100), nullable=False)
    
    # Schedule
    scheduled_date = db.Column(db.Date, nullable=False)
    scheduled_time = db.Column(db.String(20), nullable=False)
    duration_minutes = db.Column(db.Integer, default=60)
    
    # Capacity
    max_participants = db.Column(db.Integer, default=50)
    current_participants = db.Column(db.Integer, default=0)
    
    # Fees
    is_free = db.Column(db.Boolean, default=False)
    fee = db.Column(db.Float, default=0.0)
    
    # Meeting details
    meeting_link = db.Column(db.String(500), nullable=True)
    recording_link = db.Column(db.String(500), nullable=True)
    
    # Status
    status = db.Column(db.String(20), default='scheduled')  # scheduled, ongoing, completed, cancelled
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    professional = db.relationship('Professional', back_populates='webinars')
    participants = db.relationship('WebinarParticipant', back_populates='webinar')
    
    @property
    def available_spots(self):
        return self.max_participants - self.current_participants

class WebinarParticipant(db.Model):
    __tablename__ = 'webinar_participants'
    id = db.Column(db.Integer, primary_key=True)
    webinar_id = db.Column(db.Integer, db.ForeignKey('webinars.id'), nullable=False)
    client_id = db.Column(db.Integer, db.ForeignKey('clients.id'), nullable=True)
    organization_id = db.Column(db.Integer, db.ForeignKey('organizations.id'), nullable=True)
    
    # For anonymous participants
    is_anonymous = db.Column(db.Boolean, default=False)
    anonymous_name = db.Column(db.String(100), nullable=True)
    
    joined_at = db.Column(db.DateTime, default=datetime.utcnow)
    left_at = db.Column(db.DateTime, nullable=True)
    
    # Relationships
    webinar = db.relationship('Webinar', back_populates='participants')
    client = db.relationship('Client')
    organization = db.relationship('Organization')

class SessionFeedback(db.Model):
    __tablename__ = 'session_feedback'
    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.Integer, db.ForeignKey('sessions.id'), nullable=False)
    
    # Feedback
    rating = db.Column(db.Integer, nullable=False)  # 1-5
    comments = db.Column(db.Text, nullable=True)
    
    # System feedback
    system_rating = db.Column(db.Integer, nullable=True)  # Rating for the platform
    system_comments = db.Column(db.Text, nullable=True)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    session = db.relationship('Session', back_populates='feedback')

class Review(db.Model):
    __tablename__ = 'reviews'
    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.Integer, db.ForeignKey('sessions.id'), nullable=False)
    reviewer_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    reviewee_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # Review details
    rating = db.Column(db.Integer, nullable=False)  # 1-5
    comment = db.Column(db.Text, nullable=True)
    
    # Visibility
    is_public = db.Column(db.Boolean, default=True)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    session = db.relationship('Session', back_populates='review')
    reviewer = db.relationship('User', foreign_keys=[reviewer_id], back_populates='reviews_given')
    reviewee = db.relationship('User', foreign_keys=[reviewee_id], back_populates='reviews_received')

class ProfessionalAvailability(db.Model):
    __tablename__ = 'professional_availability'
    id = db.Column(db.Integer, primary_key=True)
    professional_id = db.Column(db.Integer, db.ForeignKey('professionals.id'), nullable=False)
    
    # Availability
    day_of_week = db.Column(db.Integer, nullable=False)  # 0-6 (Monday-Sunday)
    start_time = db.Column(db.String(10), nullable=False)
    end_time = db.Column(db.String(10), nullable=False)
    is_available = db.Column(db.Boolean, default=True)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    professional = db.relationship('Professional', back_populates='availability')

class WellnessAssessment(db.Model):
    __tablename__ = 'wellness_assessments'
    id = db.Column(db.Integer, primary_key=True)
    client_id = db.Column(db.Integer, db.ForeignKey('clients.id'), nullable=False)
    
    # Assessment data (stored as JSON)
    responses = db.Column(db.Text, nullable=False)  # JSON of answers
    
    # Scores
    overall_score = db.Column(db.Float, nullable=False)
    anxiety_score = db.Column(db.Float, nullable=True)
    depression_score = db.Column(db.Float, nullable=True)
    stress_score = db.Column(db.Float, nullable=True)
    sleep_score = db.Column(db.Float, nullable=True)
    
    # Risk assessment
    risk_level = db.Column(db.String(20), default='low')  # low, medium, high
    recommendations = db.Column(db.Text, nullable=True)  # JSON of recommendations
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    client = db.relationship('Client', back_populates='assessments')

class OrganizationWellnessData(db.Model):
    __tablename__ = 'organization_wellness_data'
    id = db.Column(db.Integer, primary_key=True)
    organization_id = db.Column(db.Integer, db.ForeignKey('organizations.id'), nullable=False)
    
    # Aggregated data
    month = db.Column(db.String(20), nullable=False)  # YYYY-MM
    total_employees = db.Column(db.Integer, default=0)
    active_employees = db.Column(db.Integer, default=0)
    total_sessions = db.Column(db.Integer, default=0)
    
    # Wellness metrics
    average_wellness_score = db.Column(db.Float, default=0.0)
    high_risk_count = db.Column(db.Integer, default=0)
    medium_risk_count = db.Column(db.Integer, default=0)
    low_risk_count = db.Column(db.Integer, default=0)
    
    # Department breakdown (JSON)
    department_wellness = db.Column(db.Text, nullable=True)  # JSON of department scores
    
    # Trends
    wellness_trend = db.Column(db.Text, nullable=True)  # JSON of trend data
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    organization = db.relationship('Organization', back_populates='wellness_data')

class Notification(db.Model):
    __tablename__ = 'notifications'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # Notification content
    title = db.Column(db.String(200), nullable=False)
    message = db.Column(db.Text, nullable=False)
    notification_type = db.Column(db.String(50), default='info')  # info, success, warning, alert
    icon = db.Column(db.String(50), nullable=True)
    
    # Link
    link = db.Column(db.String(500), nullable=True)
    link_text = db.Column(db.String(100), nullable=True)
    
    # Status
    is_read = db.Column(db.Boolean, default=False)
    is_important = db.Column(db.Boolean, default=False)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    read_at = db.Column(db.DateTime, nullable=True)
    
    # Relationships
    user = db.relationship('User', back_populates='notifications')
    
    def mark_as_read(self):
        self.is_read = True
        self.read_at = datetime.utcnow()

class ActivityLog(db.Model):
    __tablename__ = 'activity_logs'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    
    # Activity details
    action = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    entity_type = db.Column(db.String(50), nullable=True)
    entity_id = db.Column(db.Integer, nullable=True)
    
    # Metadata
    ip_address = db.Column(db.String(50), nullable=True)
    user_agent = db.Column(db.Text, nullable=True)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    user = db.relationship('User')

# ========== CHAT AND COMMUNITY MODELS (ADDED BACK) ==========

class ChatMessage(db.Model):
    __tablename__ = 'chat_messages'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    session_id = db.Column(db.String(100), nullable=False, index=True)
    role = db.Column(db.String(20), nullable=False)  # 'user' or 'assistant'
    content = db.Column(db.Text, nullable=False)
    is_mental_health_related = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    user = db.relationship('User', back_populates='chat_messages')
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'session_id': self.session_id,
            'role': self.role,
            'content': self.content,
            'is_mental_health_related': self.is_mental_health_related,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class CommunityPost(db.Model):
    __tablename__ = 'community_posts'
    id = db.Column(db.Integer, primary_key=True)
    author_id = db.Column(db.Integer, db.ForeignKey('clients.id'), nullable=True)
    author_name = db.Column(db.String(100), default="Anonymous")
    author_email = db.Column(db.String(120), nullable=True)
    content = db.Column(db.Text, nullable=False)
    category = db.Column(db.String(50), nullable=True)
    likes = db.Column(db.Integer, default=0)
    comments_count = db.Column(db.Integer, default=0)
    views = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_approved = db.Column(db.Boolean, default=True)
    is_featured = db.Column(db.Boolean, default=False)
    
    # Relationships
    author = db.relationship('Client', back_populates='community_posts')
    comments = db.relationship('PostComment', back_populates='post', cascade='all, delete-orphan')
    
    def to_dict(self):
        return {
            'id': self.id,
            'author': self.author_name,
            'content': self.content,
            'category': self.category,
            'likes': self.likes,
            'comments': self.comments_count,
            'date': self.created_at.strftime('%Y-%m-%d %H:%M') if self.created_at else None,
            'is_featured': self.is_featured
        }

class PostComment(db.Model):
    __tablename__ = 'post_comments'
    id = db.Column(db.Integer, primary_key=True)
    post_id = db.Column(db.Integer, db.ForeignKey('community_posts.id'), nullable=False)
    author_id = db.Column(db.Integer, db.ForeignKey('clients.id'), nullable=True)
    author_name = db.Column(db.String(100), default="Anonymous")
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    post = db.relationship('CommunityPost', back_populates='comments')
    author = db.relationship('Client', back_populates='post_comments')
    
    def to_dict(self):
        return {
            'id': self.id,
            'post_id': self.post_id,
            'author': self.author_name,
            'content': self.content,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M') if self.created_at else None
        }
