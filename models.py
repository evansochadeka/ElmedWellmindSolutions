# models.py - Complete with Enhanced Roles and Permissions
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
    
    # Enhanced Role System
    role = db.Column(db.String(50), default='client')  # superadmin, admin, organization_admin, department_head, professional, client, employee
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
    
    # Relationships
    client_profile = db.relationship('Client', foreign_keys='Client.user_id', back_populates='user', uselist=False, cascade='all, delete-orphan')
    professional_profile = db.relationship('Professional', foreign_keys='Professional.user_id', back_populates='user', uselist=False, cascade='all, delete-orphan')
    organization_profile = db.relationship('Organization', foreign_keys='Organization.user_id', back_populates='user', uselist=False, cascade='all, delete-orphan')
    department_head_profile = db.relationship('DepartmentHead', foreign_keys='DepartmentHead.user_id', back_populates='user', uselist=False, cascade='all, delete-orphan')
    notifications = db.relationship('Notification', back_populates='user', cascade='all, delete-orphan')
    reviews_given = db.relationship('Review', foreign_keys='Review.reviewer_id', back_populates='reviewer')
    reviews_received = db.relationship('Review', foreign_keys='Review.reviewee_id', back_populates='reviewee')
    chat_messages = db.relationship('ChatMessage', back_populates='user', cascade='all, delete-orphan')
    activity_logs = db.relationship('ActivityLog', back_populates='user', cascade='all, delete-orphan')
    
    # Security tokens
    reset_token = db.Column(db.String(100), nullable=True)
    reset_token_expiry = db.Column(db.DateTime, nullable=True)
    verification_token = db.Column(db.String(100), nullable=True)
    impersonated_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)  # For admin impersonation
    
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
        """Check if user has specific permission"""
        perms = json.loads(self.permissions) if self.permissions else {}
        return perms.get(permission, False)
    
    def add_permission(self, permission):
        """Add permission to user"""
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
    
    # Privacy settings - ANONYMIZED for organization views
    hide_profile = db.Column(db.Boolean, default=True)  # Hidden by default for privacy
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
    department = db.relationship('Department', foreign_keys=[department_id], back_populates='employees')
    sessions = db.relationship('Session', back_populates='client')
    session_requests = db.relationship('SessionRequest', back_populates='client')
    assessments = db.relationship('WellnessAssessment', back_populates='client')
    community_posts = db.relationship('CommunityPost', back_populates='author', cascade='all, delete-orphan')
    post_comments = db.relationship('PostComment', back_populates='author', cascade='all, delete-orphan')
    
    def get_anonymized_data(self):
        """Return anonymized data for organization viewing"""
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
    sessions = db.relationship('Session', back_populates='professional')
    session_requests = db.relationship('SessionRequest', foreign_keys='SessionRequest.professional_id', back_populates='professional')
    matched_requests = db.relationship('SessionRequest', foreign_keys='SessionRequest.matched_professional_id', backref='matched_professional_ref')
    webinars = db.relationship('Webinar', back_populates='professional')
    availability = db.relationship('ProfessionalAvailability', back_populates='professional')
    
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
    anonymize_employee_data = db.Column(db.Boolean, default=True)  # Hide personal info from org admins
    
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
    departments = db.relationship('Department', back_populates='organization')
    department_heads = db.relationship('DepartmentHead', back_populates='organization')
    wellness_data = db.relationship('OrganizationWellnessData', back_populates='organization')
    
    def generate_employee_code(self):
        self.employee_registration_code = secrets.token_hex(4).upper()
        return self.employee_registration_code
    
    def update_risk_counts(self):
        """Update risk level counts"""
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
    
    # Department head
    head_id = db.Column(db.Integer, db.ForeignKey('department_heads.id'), nullable=True)
    
    # Statistics
    employee_count = db.Column(db.Integer, default=0)
    average_wellness_score = db.Column(db.Float, default=0.0)
    high_risk_count = db.Column(db.Integer, default=0)
    medium_risk_count = db.Column(db.Integer, default=0)
    low_risk_count = db.Column(db.Integer, default=0)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    organization = db.relationship('Organization', foreign_keys=[organization_id], back_populates='departments')
    head = db.relationship('DepartmentHead', foreign_keys=[head_id], back_populates='department')
    employees = db.relationship('Client', foreign_keys='Client.department_id', back_populates='department')
    
    def update_stats(self):
        """Update department statistics"""
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
    department_id = db.Column(db.Integer, db.ForeignKey('departments.id'), nullable=True)
    
    # Permissions
    can_view_department_data = db.Column(db.Boolean, default=True)
    can_suggest_tests = db.Column(db.Boolean, default=True)
    can_view_anonymized_only = db.Column(db.Boolean, default=True)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    user = db.relationship('User', foreign_keys=[user_id], back_populates='department_head_profile')
    organization = db.relationship('Organization', foreign_keys=[organization_id], back_populates='department_heads')
    department = db.relationship('Department', foreign_keys=[department_id], back_populates='head')
    
    def get_department_stats(self):
        """Get anonymized department statistics"""
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

class SessionRequest(db.Model):
    __tablename__ = 'session_requests'
    id = db.Column(db.Integer, primary_key=True)
    client_id = db.Column(db.Integer, db.ForeignKey('clients.id'), nullable=False)
    professional_id = db.Column(db.Integer, db.ForeignKey('professionals.id'), nullable=True)
    
    # Request details
    issue_description = db.Column(db.Text, nullable=False)
    preferred_date = db.Column(db.Date, nullable=True)
    preferred_time = db.Column(db.String(20), nullable=True)
    session_type = db.Column(db.String(50), default='video')
    
    # Matching
    is_auto_matched = db.Column(db.Boolean, default=False)
    matched_professional_id = db.Column(db.Integer, db.ForeignKey('professionals.id'), nullable=True)
    matched_at = db.Column(db.DateTime, nullable=True)
    matched_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)  # Who matched (admin/auto)
    
    # Status
    status = db.Column(db.String(20), default='pending')
    expires_at = db.Column(db.DateTime, default=lambda: datetime.utcnow() + timedelta(minutes=10))
    
    # Notifications
    admin_notified = db.Column(db.Boolean, default=False)
    notification_sent_at = db.Column(db.DateTime, nullable=True)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    client = db.relationship('Client', foreign_keys=[client_id], back_populates='session_requests')
    professional = db.relationship('Professional', foreign_keys=[professional_id], back_populates='session_requests')
    matched_professional = db.relationship('Professional', foreign_keys=[matched_professional_id])
    matcher = db.relationship('User', foreign_keys=[matched_by])
    session = db.relationship('Session', back_populates='request', uselist=False)

class WellnessAssessment(db.Model):
    __tablename__ = 'wellness_assessments'
    id = db.Column(db.Integer, primary_key=True)
    client_id = db.Column(db.Integer, db.ForeignKey('clients.id'), nullable=False)
    
    # Assessment data
    responses = db.Column(db.Text, nullable=False)
    
    # Scores
    overall_score = db.Column(db.Float, nullable=False)
    anxiety_score = db.Column(db.Float, nullable=True)
    depression_score = db.Column(db.Float, nullable=True)
    stress_score = db.Column(db.Float, nullable=True)
    sleep_score = db.Column(db.Float, nullable=True)
    work_stress_score = db.Column(db.Float, nullable=True)
    relationship_score = db.Column(db.Float, nullable=True)
    
    # Risk assessment
    risk_level = db.Column(db.String(20), default='low')
    recommendations = db.Column(db.Text, nullable=True)
    
    # Suggested tests (for department heads)
    suggested_tests = db.Column(db.Text, nullable=True)
    suggested_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    client = db.relationship('Client', foreign_keys=[client_id], back_populates='assessments')
    suggester = db.relationship('User', foreign_keys=[suggested_by])

class ActivityLog(db.Model):
    __tablename__ = 'activity_logs'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    
    # Activity details
    action = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    entity_type = db.Column(db.String(50), nullable=True)
    entity_id = db.Column(db.Integer, nullable=True)
    
    # For impersonation tracking
    impersonated_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    
    # Metadata
    ip_address = db.Column(db.String(50), nullable=True)
    user_agent = db.Column(db.Text, nullable=True)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    user = db.relationship('User', foreign_keys=[user_id], back_populates='activity_logs')
    impersonator = db.relationship('User', foreign_keys=[impersonated_by])

# Keep all other existing models (Session, Webinar, Notification, etc.) from before

# ========== CHAT AND COMMUNITY MODELS ==========

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
    
    # Relationships
    author = db.relationship('Client', foreign_keys=[author_id], back_populates='community_posts')
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
