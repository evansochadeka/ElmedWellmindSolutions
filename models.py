# models.py - COMPLETE WITH ALL ORIGINAL AND NEW FEATURES - ALL RELATIONSHIPS FIXED
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
    
    # Role-based access - ENHANCED
    role = db.Column(db.String(50), default='client')  # client, professional, organization_admin, department_head, admin, superadmin
    permissions = db.Column(db.Text, default='{}')  # JSON of additional permissions
    
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
    
    # Security
    reset_token = db.Column(db.String(100), nullable=True)
    reset_token_expiry = db.Column(db.DateTime, nullable=True)
    verification_token = db.Column(db.String(100), nullable=True)
    impersonated_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)  # For admin impersonation
    
    # Relationships - FIXED with explicit foreign_keys for ALL relationships
    client_profile = db.relationship('Client', foreign_keys='Client.user_id', back_populates='user', uselist=False, cascade='all, delete-orphan')
    professional_profile = db.relationship('Professional', foreign_keys='Professional.user_id', back_populates='user', uselist=False, cascade='all, delete-orphan')
    organization_profile = db.relationship('Organization', foreign_keys='Organization.user_id', back_populates='user', uselist=False, cascade='all, delete-orphan')
    department_head_profile = db.relationship('DepartmentHead', foreign_keys='DepartmentHead.user_id', back_populates='user', uselist=False, cascade='all, delete-orphan')
    notifications = db.relationship('Notification', foreign_keys='Notification.user_id', back_populates='user', cascade='all, delete-orphan')
    reviews_given = db.relationship('Review', foreign_keys='Review.reviewer_id', back_populates='reviewer')
    reviews_received = db.relationship('Review', foreign_keys='Review.reviewee_id', back_populates='reviewee')
    chat_messages = db.relationship('ChatMessage', foreign_keys='ChatMessage.user_id', back_populates='user', cascade='all, delete-orphan')
    
    # FIXED: activity_logs relationship
    activity_logs = db.relationship('ActivityLog', 
                                   foreign_keys='ActivityLog.user_id', 
                                   back_populates='user', 
                                   cascade='all, delete-orphan')
    
    # FIXED: impersonation relationship
    impersonated_users = db.relationship('User',
                                        foreign_keys='User.impersonated_by',
                                        remote_side='User.id',
                                        backref=db.backref('impersonator', 
                                                          remote_side='User.impersonated_by'))
    
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
    
    def has_permission(self, permission):
        perms = json.loads(self.permissions) if self.permissions else {}
        return perms.get(permission, False)
    
    def add_permission(self, permission):
        perms = json.loads(self.permissions) if self.permissions else {}
        perms[permission] = True
        self.permissions = json.dumps(perms)
    
    @property
    def is_superadmin(self):
        return self.role == 'superadmin'
    
    @property
    def is_admin(self):
        return self.role in ['superadmin', 'admin']
    
    @property
    def is_organization_admin(self):
        return self.role == 'organization_admin'
    
    @property
    def is_department_head(self):
        return self.role == 'department_head'
    
    @property
    def is_professional(self):
        return self.role == 'professional'
    
    @property
    def is_client(self):
        return self.role == 'client'
    
    @property
    def is_employee(self):
        return self.role == 'employee'

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
    communication_preference = db.Column(db.String(50), default='video')
    
    # Organization association (if they belong to one)
    organization_id = db.Column(db.Integer, db.ForeignKey('organizations.id'), nullable=True)
    department_id = db.Column(db.Integer, db.ForeignKey('departments.id'), nullable=True)
    employee_id = db.Column(db.String(100), nullable=True)
    
    # Privacy settings
    hide_profile = db.Column(db.Boolean, default=True)
    allow_contact = db.Column(db.Boolean, default=False)
    
    # Wellness tracking
    wellness_score = db.Column(db.Float, default=0.0)
    risk_level = db.Column(db.String(20), default='low')
    last_assessment = db.Column(db.DateTime, nullable=True)
    assessment_count = db.Column(db.Integer, default=0)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = db.relationship('User', foreign_keys=[user_id], back_populates='client_profile')
    organization = db.relationship('Organization', foreign_keys=[organization_id], back_populates='employees')
    department = db.relationship('Department', foreign_keys=[department_id], back_populates='employees_list')
    sessions = db.relationship('Session', foreign_keys='Session.client_id', back_populates='client')
    session_requests = db.relationship('SessionRequest', foreign_keys='SessionRequest.client_id', back_populates='client')
    assessments = db.relationship('WellnessAssessment', foreign_keys='WellnessAssessment.client_id', back_populates='client')
    community_posts = db.relationship('CommunityPost', foreign_keys='CommunityPost.author_id', back_populates='author', cascade='all, delete-orphan')
    post_comments = db.relationship('PostComment', foreign_keys='PostComment.author_id', back_populates='author', cascade='all, delete-orphan')
    
    def get_anonymized_data(self):
        return {
            'id': self.id,
            'department_id': self.department_id,
            'wellness_score': self.wellness_score,
            'risk_level': self.risk_level,
            'assessment_count': self.assessment_count,
            'last_assessment': self.last_assessment.isoformat() if self.last_assessment else None,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class Professional(db.Model):
    __tablename__ = 'professionals'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, unique=True)
    
    # Professional details
    professional_type = db.Column(db.String(50), nullable=False)
    license_number = db.Column(db.String(100), nullable=False)
    years_experience = db.Column(db.Integer, nullable=True)
    specialization = db.Column(db.Text, nullable=True)
    
    # Fees
    session_fee = db.Column(db.Float, nullable=False, default=0.0)
    currency = db.Column(db.String(10), default='KES')
    
    # Document verification
    documents = db.Column(db.Text, nullable=True)
    is_verified = db.Column(db.Boolean, default=False)
    verified_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    verified_at = db.Column(db.DateTime, nullable=True)
    verification_notes = db.Column(db.Text, nullable=True)
    
    # Availability
    available_days = db.Column(db.Text, nullable=True)
    available_hours = db.Column(db.Text, nullable=True)
    
    # Statistics
    total_sessions = db.Column(db.Integer, default=0)
    average_rating = db.Column(db.Float, default=0.0)
    response_rate = db.Column(db.Float, default=0.0)
    response_time = db.Column(db.Integer, default=0)
    
    # Status
    is_available = db.Column(db.Boolean, default=True)
    accepting_clients = db.Column(db.Boolean, default=True)
    max_clients = db.Column(db.Integer, default=20)
    current_clients = db.Column(db.Integer, default=0)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = db.relationship('User', foreign_keys=[user_id], back_populates='professional_profile')
    verifier = db.relationship('User', foreign_keys=[verified_by], backref='verified_professionals')
    sessions = db.relationship('Session', foreign_keys='Session.professional_id', back_populates='professional')
    session_requests = db.relationship('SessionRequest', foreign_keys='SessionRequest.professional_id', back_populates='professional')
    matched_requests = db.relationship('SessionRequest', foreign_keys='SessionRequest.matched_professional_id', backref='matched_professional_ref')
    webinars = db.relationship('Webinar', foreign_keys='Webinar.professional_id', back_populates='professional')
    availability = db.relationship('ProfessionalAvailability', foreign_keys='ProfessionalAvailability.professional_id', back_populates='professional')
    
    @property
    def client_facing_fee(self):
        return self.session_fee * 1.2
    
    def get_specializations(self):
        if self.specialization:
            return json.loads(self.specialization)
        return []
    
    def can_accept_new_client(self):
        return self.accepting_clients and self.current_clients < self.max_clients

class Organization(db.Model):
    __tablename__ = 'organizations'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, unique=True)
    
    # Organization details
    company_name = db.Column(db.String(200), nullable=False)
    registration_number = db.Column(db.String(100), nullable=False)
    industry = db.Column(db.String(100), nullable=True)
    company_size = db.Column(db.Integer, default=0)
    
    # Registration code for employees
    employee_registration_code = db.Column(db.String(50), unique=True, nullable=True)
    
    # Privacy settings
    anonymize_employee_data = db.Column(db.Boolean, default=True)
    
    # Statistics
    total_employees = db.Column(db.Integer, default=0)
    active_this_month = db.Column(db.Integer, default=0)
    total_sessions = db.Column(db.Integer, default=0)
    average_wellness_score = db.Column(db.Float, default=0.0)
    high_risk_employees = db.Column(db.Integer, default=0)
    medium_risk_employees = db.Column(db.Integer, default=0)
    low_risk_employees = db.Column(db.Integer, default=0)
    
    # Settings
    allow_anonymous_sessions = db.Column(db.Boolean, default=True)
    hide_employee_issues = db.Column(db.Boolean, default=True)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = db.relationship('User', foreign_keys=[user_id], back_populates='organization_profile')
    employees = db.relationship('Client', foreign_keys='Client.organization_id', back_populates='organization')
    departments = db.relationship('Department', foreign_keys='Department.organization_id', back_populates='organization')
    department_heads = db.relationship('DepartmentHead', foreign_keys='DepartmentHead.organization_id', back_populates='organization')
    wellness_data = db.relationship('OrganizationWellnessData', foreign_keys='OrganizationWellnessData.organization_id', back_populates='organization')
    
    def generate_employee_code(self):
        self.employee_registration_code = secrets.token_hex(4).upper()
        return self.employee_registration_code
    
    def update_risk_counts(self):
        self.high_risk_employees = Client.query.filter_by(organization_id=self.id, risk_level='high').count()
        self.medium_risk_employees = Client.query.filter_by(organization_id=self.id, risk_level='medium').count()
        self.low_risk_employees = Client.query.filter_by(organization_id=self.id, risk_level='low').count()
        db.session.commit()

class Department(db.Model):
    __tablename__ = 'departments'
    id = db.Column(db.Integer, primary_key=True)
    organization_id = db.Column(db.Integer, db.ForeignKey('organizations.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    
    # Department head - FIXED: Remove circular dependency
    head_id = db.Column(db.Integer, nullable=True)  # Temporarily remove FK constraint
    
    # Statistics
    employee_count = db.Column(db.Integer, default=0)
    average_wellness_score = db.Column(db.Float, default=0.0)
    high_risk_count = db.Column(db.Integer, default=0)
    medium_risk_count = db.Column(db.Integer, default=0)
    low_risk_count = db.Column(db.Integer, default=0)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships - FIXED: Remove circular backrefs
    organization = db.relationship('Organization', foreign_keys=[organization_id], back_populates='departments')
    employees_list = db.relationship('Client', foreign_keys='Client.department_id', back_populates='department')
    
    # FIXED: Add relationship to department head without circular dependency
    head = db.relationship('DepartmentHead', foreign_keys='DepartmentHead.department_id', uselist=False)
    
    def update_stats(self):
        employees = Client.query.filter_by(department_id=self.id).all()
        self.employee_count = len(employees)
        
        if employees:
            self.average_wellness_score = sum(e.wellness_score for e in employees) / len(employees)
            self.high_risk_count = sum(1 for e in employees if e.risk_level == 'high')
            self.medium_risk_count = sum(1 for e in employees if e.risk_level == 'medium')
            self.low_risk_count = sum(1 for e in employees if e.risk_level == 'low')
        
        db.session.commit()

class DepartmentHead(db.Model):
    __tablename__ = 'department_heads'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, unique=True)
    organization_id = db.Column(db.Integer, db.ForeignKey('organizations.id'), nullable=False)
    department_id = db.Column(db.Integer, db.ForeignKey('departments.id'), nullable=True, unique=True)
    
    # Permissions
    can_view_department_data = db.Column(db.Boolean, default=True)
    can_suggest_tests = db.Column(db.Boolean, default=True)
    can_view_anonymized_only = db.Column(db.Boolean, default=True)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships - FIXED: No circular backrefs
    user = db.relationship('User', foreign_keys=[user_id], back_populates='department_head_profile')
    organization = db.relationship('Organization', foreign_keys=[organization_id], back_populates='department_heads')
    department = db.relationship('Department', foreign_keys=[department_id], backref='department_head_ref')
    
    def get_department_stats(self):
        if not self.department:
            return None
        
        employees = Client.query.filter_by(department_id=self.department.id).all()
        
        return {
            'total_employees': len(employees),
            'average_wellness_score': self.department.average_wellness_score,
            'risk_distribution': {
                'high': self.department.high_risk_count,
                'medium': self.department.medium_risk_count,
                'low': self.department.low_risk_count
            },
            'assessment_completion': sum(1 for e in employees if e.assessment_count > 0),
            'active_users': sum(1 for e in employees if e.user.last_active and 
                               e.user.last_active > datetime.utcnow() - timedelta(days=30))
        }

# ========== ORIGINAL CHAT AND COMMUNITY MODELS ==========

class ChatMessage(db.Model):
    __tablename__ = 'chat_messages'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    session_id = db.Column(db.String(100), nullable=False, index=True)
    role = db.Column(db.String(20), nullable=False)
    content = db.Column(db.Text, nullable=False)
    is_mental_health_related = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    user = db.relationship('User', foreign_keys=[user_id], back_populates='chat_messages')
    
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
    
    author = db.relationship('Client', foreign_keys=[author_id], back_populates='community_posts')
    comments = db.relationship('PostComment', foreign_keys='PostComment.post_id', back_populates='post', cascade='all, delete-orphan')
    
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
    
    post = db.relationship('CommunityPost', foreign_keys=[post_id], back_populates='comments')
    author = db.relationship('Client', foreign_keys=[author_id], back_populates='post_comments')
    
    def to_dict(self):
        return {
            'id': self.id,
            'post_id': self.post_id,
            'author': self.author_name,
            'content': self.content,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M') if self.created_at else None
        }

# ========== SESSION AND APPOINTMENT MODELS ==========

class SessionRequest(db.Model):
    __tablename__ = 'session_requests'
    id = db.Column(db.Integer, primary_key=True)
    client_id = db.Column(db.Integer, db.ForeignKey('clients.id'), nullable=False)
    professional_id = db.Column(db.Integer, db.ForeignKey('professionals.id'), nullable=True)
    
    issue_description = db.Column(db.Text, nullable=False)
    preferred_date = db.Column(db.Date, nullable=True)
    preferred_time = db.Column(db.String(20), nullable=True)
    session_type = db.Column(db.String(50), default='video')
    
    is_auto_matched = db.Column(db.Boolean, default=False)
    matched_professional_id = db.Column(db.Integer, db.ForeignKey('professionals.id'), nullable=True)
    matched_at = db.Column(db.DateTime, nullable=True)
    matched_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    
    status = db.Column(db.String(20), default='pending')
    expires_at = db.Column(db.DateTime, default=lambda: datetime.utcnow() + timedelta(minutes=10))
    
    admin_notified = db.Column(db.Boolean, default=False)
    notification_sent_at = db.Column(db.DateTime, nullable=True)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    client = db.relationship('Client', foreign_keys=[client_id], back_populates='session_requests')
    professional = db.relationship('Professional', foreign_keys=[professional_id], back_populates='session_requests')
    matched_professional = db.relationship('Professional', foreign_keys=[matched_professional_id])
    matcher = db.relationship('User', foreign_keys=[matched_by])
    session = db.relationship('Session', foreign_keys='Session.request_id', back_populates='request', uselist=False)

class Session(db.Model):
    __tablename__ = 'sessions'
    id = db.Column(db.Integer, primary_key=True)
    request_id = db.Column(db.Integer, db.ForeignKey('session_requests.id'), nullable=True)
    client_id = db.Column(db.Integer, db.ForeignKey('clients.id'), nullable=False)
    professional_id = db.Column(db.Integer, db.ForeignKey('professionals.id'), nullable=False)
    
    session_type = db.Column(db.String(50), nullable=False)
    title = db.Column(db.String(200), nullable=True)
    description = db.Column(db.Text, nullable=True)
    
    scheduled_date = db.Column(db.Date, nullable=False)
    scheduled_time = db.Column(db.String(20), nullable=False)
    duration_minutes = db.Column(db.Integer, default=60)
    
    professional_fee = db.Column(db.Float, nullable=False)
    platform_fee = db.Column(db.Float, nullable=False)
    total_fee = db.Column(db.Float, nullable=False)
    
    meeting_link = db.Column(db.String(500), nullable=True)
    meeting_password = db.Column(db.String(100), nullable=True)
    
    status = db.Column(db.String(20), default='scheduled')
    cancellation_reason = db.Column(db.Text, nullable=True)
    
    is_anonymous = db.Column(db.Boolean, default=False)
    hide_contact = db.Column(db.Boolean, default=True)
    
    started_at = db.Column(db.DateTime, nullable=True)
    completed_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    client = db.relationship('Client', foreign_keys=[client_id], back_populates='sessions')
    professional = db.relationship('Professional', foreign_keys=[professional_id], back_populates='sessions')
    request = db.relationship('SessionRequest', foreign_keys=[request_id], back_populates='session')
    feedback = db.relationship('SessionFeedback', foreign_keys='SessionFeedback.session_id', back_populates='session', uselist=False)
    review = db.relationship('Review', foreign_keys='Review.session_id', back_populates='session', uselist=False)

class Webinar(db.Model):
    __tablename__ = 'webinars'
    id = db.Column(db.Integer, primary_key=True)
    professional_id = db.Column(db.Integer, db.ForeignKey('professionals.id'), nullable=False)
    
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    topic = db.Column(db.String(100), nullable=False)
    
    scheduled_date = db.Column(db.Date, nullable=False)
    scheduled_time = db.Column(db.String(20), nullable=False)
    duration_minutes = db.Column(db.Integer, default=60)
    
    max_participants = db.Column(db.Integer, default=50)
    current_participants = db.Column(db.Integer, default=0)
    
    is_free = db.Column(db.Boolean, default=False)
    fee = db.Column(db.Float, default=0.0)
    
    meeting_link = db.Column(db.String(500), nullable=True)
    recording_link = db.Column(db.String(500), nullable=True)
    
    status = db.Column(db.String(20), default='scheduled')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    professional = db.relationship('Professional', foreign_keys=[professional_id], back_populates='webinars')
    participants = db.relationship('WebinarParticipant', foreign_keys='WebinarParticipant.webinar_id', back_populates='webinar')
    
    @property
    def available_spots(self):
        return self.max_participants - self.current_participants

class WebinarParticipant(db.Model):
    __tablename__ = 'webinar_participants'
    id = db.Column(db.Integer, primary_key=True)
    webinar_id = db.Column(db.Integer, db.ForeignKey('webinars.id'), nullable=False)
    client_id = db.Column(db.Integer, db.ForeignKey('clients.id'), nullable=True)
    organization_id = db.Column(db.Integer, db.ForeignKey('organizations.id'), nullable=True)
    
    is_anonymous = db.Column(db.Boolean, default=False)
    anonymous_name = db.Column(db.String(100), nullable=True)
    
    joined_at = db.Column(db.DateTime, default=datetime.utcnow)
    left_at = db.Column(db.DateTime, nullable=True)
    
    webinar = db.relationship('Webinar', foreign_keys=[webinar_id], back_populates='participants')
    client = db.relationship('Client', foreign_keys=[client_id])
    organization = db.relationship('Organization', foreign_keys=[organization_id])

# ========== FEEDBACK AND REVIEW MODELS ==========

class SessionFeedback(db.Model):
    __tablename__ = 'session_feedback'
    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.Integer, db.ForeignKey('sessions.id'), nullable=False)
    
    rating = db.Column(db.Integer, nullable=False)
    comments = db.Column(db.Text, nullable=True)
    
    system_rating = db.Column(db.Integer, nullable=True)
    system_comments = db.Column(db.Text, nullable=True)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    session = db.relationship('Session', foreign_keys=[session_id], back_populates='feedback')

class Review(db.Model):
    __tablename__ = 'reviews'
    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.Integer, db.ForeignKey('sessions.id'), nullable=False)
    reviewer_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    reviewee_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    rating = db.Column(db.Integer, nullable=False)
    comment = db.Column(db.Text, nullable=True)
    
    is_public = db.Column(db.Boolean, default=True)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    session = db.relationship('Session', foreign_keys=[session_id], back_populates='review')
    reviewer = db.relationship('User', foreign_keys=[reviewer_id], back_populates='reviews_given')
    reviewee = db.relationship('User', foreign_keys=[reviewee_id], back_populates='reviews_received')

# ========== WELLNESS ASSESSMENT MODELS ==========

class WellnessAssessment(db.Model):
    __tablename__ = 'wellness_assessments'
    id = db.Column(db.Integer, primary_key=True)
    client_id = db.Column(db.Integer, db.ForeignKey('clients.id'), nullable=False)
    
    responses = db.Column(db.Text, nullable=False)
    
    overall_score = db.Column(db.Float, nullable=False)
    anxiety_score = db.Column(db.Float, nullable=True)
    depression_score = db.Column(db.Float, nullable=True)
    stress_score = db.Column(db.Float, nullable=True)
    sleep_score = db.Column(db.Float, nullable=True)
    work_stress_score = db.Column(db.Float, nullable=True)
    relationship_score = db.Column(db.Float, nullable=True)
    
    risk_level = db.Column(db.String(20), default='low')
    recommendations = db.Column(db.Text, nullable=True)
    
    suggested_tests = db.Column(db.Text, nullable=True)
    suggested_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    client = db.relationship('Client', foreign_keys=[client_id], back_populates='assessments')
    suggester = db.relationship('User', foreign_keys=[suggested_by])

class OrganizationWellnessData(db.Model):
    __tablename__ = 'organization_wellness_data'
    id = db.Column(db.Integer, primary_key=True)
    organization_id = db.Column(db.Integer, db.ForeignKey('organizations.id'), nullable=False)
    
    month = db.Column(db.String(20), nullable=False)
    total_employees = db.Column(db.Integer, default=0)
    active_employees = db.Column(db.Integer, default=0)
    total_sessions = db.Column(db.Integer, default=0)
    
    average_wellness_score = db.Column(db.Float, default=0.0)
    high_risk_count = db.Column(db.Integer, default=0)
    medium_risk_count = db.Column(db.Integer, default=0)
    low_risk_count = db.Column(db.Integer, default=0)
    
    department_wellness = db.Column(db.Text, nullable=True)
    wellness_trend = db.Column(db.Text, nullable=True)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    organization = db.relationship('Organization', foreign_keys=[organization_id], back_populates='wellness_data')

# ========== PROFESSIONAL AVAILABILITY ==========

class ProfessionalAvailability(db.Model):
    __tablename__ = 'professional_availability'
    id = db.Column(db.Integer, primary_key=True)
    professional_id = db.Column(db.Integer, db.ForeignKey('professionals.id'), nullable=False)
    
    day_of_week = db.Column(db.Integer, nullable=False)
    start_time = db.Column(db.String(10), nullable=False)
    end_time = db.Column(db.String(10), nullable=False)
    is_available = db.Column(db.Boolean, default=True)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    professional = db.relationship('Professional', foreign_keys=[professional_id], back_populates='availability')

# ========== NOTIFICATION AND ACTIVITY MODELS ==========

class Notification(db.Model):
    __tablename__ = 'notifications'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    title = db.Column(db.String(200), nullable=False)
    message = db.Column(db.Text, nullable=False)
    notification_type = db.Column(db.String(50), default='info')
    icon = db.Column(db.String(50), nullable=True)
    
    link = db.Column(db.String(500), nullable=True)
    link_text = db.Column(db.String(100), nullable=True)
    
    is_read = db.Column(db.Boolean, default=False)
    is_important = db.Column(db.Boolean, default=False)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    read_at = db.Column(db.DateTime, nullable=True)
    
    user = db.relationship('User', foreign_keys=[user_id], back_populates='notifications')
    
    def mark_as_read(self):
        self.is_read = True
        self.read_at = datetime.utcnow()

class Complaint(db.Model):
    __tablename__ = 'complaints'
    id = db.Column(db.Integer, primary_key=True)
    organization_id = db.Column(db.Integer, db.ForeignKey('organizations.id'), nullable=False)
    professional_id = db.Column(db.Integer, db.ForeignKey('professionals.id'), nullable=False)
    
    type = db.Column(db.String(50), nullable=False)  # unprofessional, missed_session, late, billing, other
    description = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(20), default='pending')  # pending, reviewed, resolved, dismissed
    response = db.Column(db.Text, nullable=True)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    organization = db.relationship('Organization', backref='complaints')
    professional = db.relationship('Professional', backref='complaints')
class ActivityLog(db.Model):
    __tablename__ = 'activity_logs'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    
    action = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    entity_type = db.Column(db.String(50), nullable=True)
    entity_id = db.Column(db.Integer, nullable=True)
    
    impersonated_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    
    ip_address = db.Column(db.String(50), nullable=True)
    user_agent = db.Column(db.Text, nullable=True)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # FIXED: Relationships with explicit foreign_keys
    user = db.relationship('User', foreign_keys=[user_id], back_populates='activity_logs')
    impersonator = db.relationship('User', foreign_keys=[impersonated_by], backref='impersonation_logs')
