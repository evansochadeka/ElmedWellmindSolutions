# auth_routes.py - COMPLETE with login and all features
from flask import Blueprint, render_template, request, jsonify, redirect, url_for, session
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.utils import secure_filename
from models import db, User, Client, Professional, Organization, Department, Notification, ActivityLog
from datetime import datetime, timedelta
import secrets
import os
import json
import re

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')

# Validation functions
EMAIL_REGEX = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
PHONE_REGEX = re.compile(r'^(\+254|0)[0-9]{9}$')

def validate_email(email):
    return bool(EMAIL_REGEX.match(email))

def validate_phone(phone):
    return bool(PHONE_REGEX.match(phone))

def save_uploaded_file(file, user_id, file_type):
    """Save uploaded file and return filename"""
    if file and file.filename:
        filename = secure_filename(f"{user_id}_{file_type}_{file.filename}")
        file_path = os.path.join('static', 'uploads', file_type, filename)
        file.save(file_path)
        return filename
    return None

def create_notification(user_id, title, message, notification_type='info', link=None):
    """Create a notification for a user"""
    notification = Notification(
        user_id=user_id,
        title=title,
        message=message,
        notification_type=notification_type,
        link=link
    )
    db.session.add(notification)
    db.session.commit()

def log_activity(user_id, action, description=None, entity_type=None, entity_id=None):
    """Log user activity"""
    log = ActivityLog(
        user_id=user_id,
        action=action,
        description=description,
        entity_type=entity_type,
        entity_id=entity_id,
        ip_address=request.remote_addr,
        user_agent=request.user_agent.string if request.user_agent else None
    )
    db.session.add(log)
    db.session.commit()

# Registration page with role selection
@auth_bp.route('/register')
def register_page():
    """Registration page"""
    if current_user.is_authenticated:
        return redirect(url_for('dashboard_redirect'))
    return render_template('auth/register.html')

# Login page
@auth_bp.route('/login')
def login_page():
    """Login page"""
    if current_user.is_authenticated:
        return redirect(url_for('dashboard_redirect'))
    return render_template('auth/login.html')

# Get started redirect
@auth_bp.route('/get-started')
def get_started():
    """Get started redirect"""
    return redirect(url_for('auth.register_page'))

# API: Login
@auth_bp.route('/api/login', methods=['POST'])
def api_login():
    """Login user"""
    try:
        data = request.json
        email = data.get('email')
        password = data.get('password')
        remember = data.get('remember', False)
        
        if not email or not password:
            return jsonify({'success': False, 'message': 'Email and password required'}), 400
        
        # Find user
        user = User.query.filter_by(email=email).first()
        
        if not user or not user.check_password(password):
            return jsonify({'success': False, 'message': 'Invalid email or password'}), 401
        
        if not user.is_active:
            return jsonify({'success': False, 'message': 'Account is deactivated. Contact support.'}), 403
        
        # Update last login
        user.last_login = datetime.utcnow()
        user.last_active = datetime.utcnow()
        db.session.commit()
        
        # Login user
        login_user(user, remember=remember)
        
        # Log activity
        log_activity(user.id, 'LOGIN', 'User logged in')
        
        # Determine redirect based on role
        if user.role == 'admin':
            redirect_url = url_for('admin.dashboard')
        elif user.role == 'professional':
            redirect_url = url_for('professional.dashboard')
        elif user.role == 'organization':
            redirect_url = url_for('organization.dashboard')
        else:
            redirect_url = url_for('client_dashboard')
        
        return jsonify({
            'success': True,
            'message': 'Login successful!',
            'redirect': redirect_url,
            'user': {
                'id': user.id,
                'name': user.get_full_name(),
                'email': user.email,
                'role': user.role
            }
        })
        
    except Exception as e:
        print(f"Login error: {str(e)}")
        return jsonify({'success': False, 'message': 'Login failed. Please try again.'}), 500

# API: Logout
@auth_bp.route('/api/logout', methods=['POST'])
@login_required
def api_logout():
    """Logout user"""
    log_activity(current_user.id, 'LOGOUT', 'User logged out')
    logout_user()
    return jsonify({'success': True, 'message': 'Logged out successfully'})

# API: Register client
@auth_bp.route('/api/register/client', methods=['POST'])
def api_register_client():
    try:
        data = request.json
        
        # Validate required fields
        required = ['first_name', 'last_name', 'email', 'password']
        for field in required:
            if not data.get(field):
                return jsonify({'success': False, 'message': f'{field} is required'}), 400
        
        # Validate email
        if not validate_email(data['email']):
            return jsonify({'success': False, 'message': 'Invalid email format'}), 400
        
        # Check if user exists
        if User.query.filter_by(email=data['email']).first():
            return jsonify({'success': False, 'message': 'Email already registered'}), 400
        
        # Create user
        user = User(
            username=data['email'].split('@')[0] + secrets.token_hex(2),
            email=data['email'],
            first_name=data['first_name'],
            last_name=data['last_name'],
            phone=data.get('phone', ''),
            role='client'
        )
        user.set_password(data['password'])
        
        db.session.add(user)
        db.session.flush()
        
        # Create client profile
        client = Client(
            user_id=user.id,
            brief_issue=data.get('brief_issue', ''),
            emergency_contact=data.get('emergency_contact', ''),
            emergency_contact_name=data.get('emergency_contact_name', '')
        )
        
        # If they have organization code
        if data.get('organization_code'):
            org = Organization.query.filter_by(employee_registration_code=data['organization_code']).first()
            if org:
                client.organization_id = org.id
                client.department = data.get('department', '')
                client.employee_id = data.get('employee_id', '')
                
                # Update organization stats
                org.total_employees += 1
                
                # Create department if needed
                if data.get('department'):
                    dept = Department.query.filter_by(
                        organization_id=org.id,
                        name=data['department']
                    ).first()
                    if not dept:
                        dept = Department(
                            organization_id=org.id,
                            name=data['department']
                        )
                        db.session.add(dept)
                    dept.employee_count += 1
        
        db.session.add(client)
        db.session.commit()
        
        # Log activity
        log_activity(user.id, 'REGISTER', f'Client registered', 'user', user.id)
        
        # Create welcome notification
        create_notification(
            user.id,
            'Welcome to Elmed Wellmind!',
            'Thank you for registering. Start your wellness journey today.',
            'success',
            '/dashboard/client'
        )
        
        return jsonify({
            'success': True,
            'message': 'Registration successful! Please login.',
            'redirect': url_for('auth.login_page')
        })
        
    except Exception as e:
        db.session.rollback()
        print(f"Client registration error: {str(e)}")
        return jsonify({'success': False, 'message': 'Registration failed. Please try again.'}), 500

# API: Register professional
@auth_bp.route('/api/register/professional', methods=['POST'])
def api_register_professional():
    try:
        # Handle multipart form data
        first_name = request.form.get('first_name')
        last_name = request.form.get('last_name')
        email = request.form.get('email')
        phone = request.form.get('phone')
        professional_type = request.form.get('professional_type')
        license_number = request.form.get('license_number')
        years_experience = request.form.get('years_experience', 0)
        specializations = request.form.get('specializations', '[]')
        session_fee = request.form.get('session_fee')
        password = request.form.get('password')
        
        # Validate required fields
        if not all([first_name, last_name, email, professional_type, license_number, session_fee, password]):
            return jsonify({'success': False, 'message': 'All required fields must be filled'}), 400
        
        # Validate email
        if not validate_email(email):
            return jsonify({'success': False, 'message': 'Invalid email format'}), 400
        
        # Check if user exists
        if User.query.filter_by(email=email).first():
            return jsonify({'success': False, 'message': 'Email already registered'}), 400
        
        # Create user
        user = User(
            username=email.split('@')[0] + secrets.token_hex(2),
            email=email,
            first_name=first_name,
            last_name=last_name,
            phone=phone,
            role='professional'
        )
        user.set_password(password)
        
        db.session.add(user)
        db.session.flush()
        
        # Handle document uploads
        documents = []
        if 'documents' in request.files:
            files = request.files.getlist('documents')
            for file in files:
                if file and file.filename:
                    filename = save_uploaded_file(file, user.id, 'documents')
                    if filename:
                        documents.append(filename)
        
        # Create professional profile
        professional = Professional(
            user_id=user.id,
            professional_type=professional_type,
            license_number=license_number,
            years_experience=int(years_experience) if years_experience else 0,
            specialization=specializations,
            session_fee=float(session_fee),
            documents=json.dumps(documents),
            is_verified=False  # Requires admin approval
        )
        
        db.session.add(professional)
        db.session.commit()
        
        # Log activity
        log_activity(user.id, 'REGISTER', f'Professional registered', 'user', user.id)
        
        # Notify admins
        admins = User.query.filter_by(role='admin').all()
        for admin in admins:
            create_notification(
                admin.id,
                'New Professional Registration',
                f'{user.get_full_name()} has registered as a {professional_type}.',
                'info',
                '/admin/professionals'
            )
        
        return jsonify({
            'success': True,
            'message': 'Registration successful! Your account will be verified by admin.',
            'redirect': url_for('auth.login_page')
        })
        
    except Exception as e:
        db.session.rollback()
        print(f"Professional registration error: {str(e)}")
        return jsonify({'success': False, 'message': 'Registration failed. Please try again.'}), 500

# API: Register organization
@auth_bp.route('/api/register/organization', methods=['POST'])
def api_register_organization():
    try:
        data = request.json
        
        # Verify registration code
        if data.get('registration_code') != 'Papai123':
            return jsonify({'success': False, 'message': 'Invalid registration code'}), 400
        
        # Validate required fields
        required = ['company_name', 'registration_number', 'employee_count', 'contact_person', 'email', 'phone', 'password']
        for field in required:
            if not data.get(field):
                return jsonify({'success': False, 'message': f'{field} is required'}), 400
        
        # Validate email
        if not validate_email(data['email']):
            return jsonify({'success': False, 'message': 'Invalid email format'}), 400
        
        # Check if user exists
        if User.query.filter_by(email=data['email']).first():
            return jsonify({'success': False, 'message': 'Email already registered'}), 400
        
        # Create user (contact person)
        user = User(
            username=data['email'].split('@')[0] + secrets.token_hex(2),
            email=data['email'],
            first_name=data['contact_person'].split()[0] if ' ' in data['contact_person'] else data['contact_person'],
            last_name=data['contact_person'].split()[-1] if len(data['contact_person'].split()) > 1 else '',
            phone=data['phone'],
            role='organization'
        )
        user.set_password(data['password'])
        
        db.session.add(user)
        db.session.flush()
        
        # Generate employee registration code
        employee_code = secrets.token_hex(4).upper()
        
        # Create organization profile
        organization = Organization(
            user_id=user.id,
            company_name=data['company_name'],
            registration_number=data['registration_number'],
            industry=data.get('industry', ''),
            company_size=int(data['employee_count']),
            employee_registration_code=employee_code
        )
        
        db.session.add(organization)
        db.session.commit()
        
        # Log activity
        log_activity(user.id, 'REGISTER', f'Organization registered', 'organization', organization.id)
        
        return jsonify({
            'success': True,
            'message': 'Organization registered successfully!',
            'employee_code': employee_code,
            'redirect': url_for('auth.login_page')
        })
        
    except Exception as e:
        db.session.rollback()
        print(f"Organization registration error: {str(e)}")
        return jsonify({'success': False, 'message': 'Registration failed. Please try again.'}), 500

# API: Get current user
@auth_bp.route('/api/me', methods=['GET'])
@login_required
def api_get_current_user():
    """Get current user info"""
    user_data = {
        'id': current_user.id,
        'username': current_user.username,
        'email': current_user.email,
        'first_name': current_user.first_name,
        'last_name': current_user.last_name,
        'full_name': current_user.get_full_name(),
        'phone': current_user.phone,
        'role': current_user.role,
        'is_verified': current_user.is_verified,
        'email_verified': current_user.email_verified,
        'profile_pic': current_user.profile_pic,
        'created_at': current_user.created_at.isoformat() if current_user.created_at else None,
        'last_login': current_user.last_login.isoformat() if current_user.last_login else None
    }
    
    # Add role-specific data
    if current_user.role == 'professional' and current_user.professional_profile:
        prof = current_user.professional_profile
        user_data['professional'] = {
            'id': prof.id,
            'type': prof.professional_type,
            'is_verified': prof.is_verified,
            'session_fee': prof.session_fee,
            'client_facing_fee': prof.client_facing_fee,
            'average_rating': prof.average_rating
        }
    
    elif current_user.role == 'organization' and current_user.organization_profile:
        org = current_user.organization_profile
        user_data['organization'] = {
            'id': org.id,
            'company_name': org.company_name,
            'employee_code': org.employee_registration_code,
            'total_employees': org.total_employees
        }
    
    elif current_user.role == 'client' and current_user.client_profile:
        client = current_user.client_profile
        user_data['client'] = {
            'id': client.id,
            'organization_id': client.organization_id,
            'department': client.department,
            'wellness_score': client.wellness_score
        }
    
    return jsonify(user_data)

# API: Forgot password
@auth_bp.route('/api/forgot-password', methods=['POST'])
def api_forgot_password():
    """Handle forgot password request"""
    try:
        data = request.json
        email = data.get('email')
        
        user = User.query.filter_by(email=email).first()
        if user:
            token = user.generate_reset_token()
            db.session.commit()
            
            # Here you would send email with reset link
            print(f"Password reset token for {email}: {token}")
            
            return jsonify({
                'success': True,
                'message': 'Password reset instructions sent to your email'
            })
        else:
            return jsonify({'success': False, 'message': 'Email not found'}), 404
            
    except Exception as e:
        print(f"Forgot password error: {str(e)}")
        return jsonify({'success': False, 'message': 'Failed to process request'}), 500

# API: Reset password
@auth_bp.route('/api/reset-password', methods=['POST'])
def api_reset_password():
    """Reset password with token"""
    try:
        data = request.json
        token = data.get('token')
        new_password = data.get('password')
        
        user = User.query.filter_by(reset_token=token).first()
        if not user or not user.verify_reset_token(token):
            return jsonify({'success': False, 'message': 'Invalid or expired token'}), 400
        
        user.set_password(new_password)
        user.reset_token = None
        user.reset_token_expiry = None
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Password reset successful'})
        
    except Exception as e:
        print(f"Reset password error: {str(e)}")
        return jsonify({'success': False, 'message': 'Failed to reset password'}), 500

# API: Check session
@auth_bp.route('/api/session', methods=['GET'])
def api_check_session():
    """Check if user is authenticated"""
    if current_user.is_authenticated:
        return jsonify({
            'authenticated': True,
            'user_id': current_user.id,
            'role': current_user.role
        })
    return jsonify({'authenticated': False})
