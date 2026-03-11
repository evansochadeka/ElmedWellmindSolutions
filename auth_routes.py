# auth_routes.py - COMPLETE WITH ALL FEATURES - FIXED DUPLICATE FUNCTION
from flask import Blueprint, render_template, request, jsonify, redirect, url_for, session
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.utils import secure_filename
from models import db, User, Client, Professional, Organization, Department, DepartmentHead, Notification, ActivityLog
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
def register():
    """Registration page"""
    if current_user.is_authenticated:
        return redirect(url_for('dashboard_redirect'))
    return render_template('auth/register.html')

# Login page
@auth_bp.route('/login')
def login():
    """Login page"""
    if current_user.is_authenticated:
        return redirect(url_for('dashboard_redirect'))
    return render_template('auth/login.html')

# Get started redirect
@auth_bp.route('/get-started')
def get_started():
    """Get started redirect"""
    return redirect(url_for('auth.register'))

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
        if user.role == 'superadmin':
            redirect_url = url_for('superadmin.dashboard')
        elif user.role == 'admin':
            redirect_url = url_for('admin.dashboard')
        elif user.role == 'professional':
            redirect_url = url_for('professional.dashboard')
        elif user.role == 'organization_admin':
            redirect_url = url_for('organization.dashboard')
        elif user.role == 'org_manager':
            redirect_url = url_for('organization.manager_dashboard')
        elif user.role == 'org_hr':
            redirect_url = url_for('organization.hr_dashboard')
        elif user.role == 'org_supervisor':
            redirect_url = url_for('organization.supervisor_dashboard')
        elif user.role == 'org_employee':
            redirect_url = url_for('organization.employee_dashboard')
        elif user.role == 'department_head':
            redirect_url = url_for('dept_head.dashboard')
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
    session.clear()
    return jsonify({'success': True, 'message': 'Logged out successfully'})

# API: Register client
@auth_bp.route('/api/register/client', methods=['POST'])
def api_register_client():
    """Register a new client"""
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
        
        # Validate phone if provided
        if data.get('phone') and not validate_phone(data['phone']):
            return jsonify({'success': False, 'message': 'Invalid phone number format. Use +254XXXXXXXXX or 07XXXXXXXX'}), 400
        
        # Check if user exists
        if User.query.filter_by(email=data['email']).first():
            return jsonify({'success': False, 'message': 'Email already registered'}), 400
        
        # Create username
        base_username = data['email'].split('@')[0]
        username = base_username
        counter = 1
        while User.query.filter_by(username=username).first():
            username = f"{base_username}{counter}"
            counter += 1
        
        # Create user
        user = User(
            username=username,
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
            'redirect': url_for('auth.login')
        })
        
    except Exception as e:
        db.session.rollback()
        print(f"Client registration error: {str(e)}")
        return jsonify({'success': False, 'message': 'Registration failed. Please try again.'}), 500

# API: Register professional
@auth_bp.route('/api/register/professional', methods=['POST'])
def api_register_professional():
    """Register a new professional with profile photo"""
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
        bio = request.form.get('bio', '')
        password = request.form.get('password')
        
        # Validate required fields
        if not all([first_name, last_name, email, professional_type, license_number, session_fee, password]):
            return jsonify({'success': False, 'message': 'All required fields must be filled'}), 400
        
        # Validate email
        if not validate_email(email):
            return jsonify({'success': False, 'message': 'Invalid email format'}), 400
        
        # Validate phone
        if not validate_phone(phone):
            return jsonify({'success': False, 'message': 'Invalid phone number format. Use +254XXXXXXXXX or 07XXXXXXXX'}), 400
        
        # Check if user exists
        if User.query.filter_by(email=email).first():
            return jsonify({'success': False, 'message': 'Email already registered'}), 400
        
        # Check license number uniqueness
        if Professional.query.filter_by(license_number=license_number).first():
            return jsonify({'success': False, 'message': 'This license number is already registered'}), 400
        
        # Create username
        base_username = email.split('@')[0]
        username = base_username
        counter = 1
        while User.query.filter_by(username=username).first():
            username = f"{base_username}{counter}"
            counter += 1
        
        # Handle profile photo upload
        profile_photo = 'default-professional.jpg'  # Default photo
        if 'profile_photo' in request.files:
            photo = request.files['profile_photo']
            if photo and photo.filename:
                # Validate file type
                allowed_extensions = {'png', 'jpg', 'jpeg', 'gif'}
                ext = photo.filename.rsplit('.', 1)[1].lower() if '.' in photo.filename else ''
                
                if ext not in allowed_extensions:
                    return jsonify({'success': False, 'message': 'Profile photo must be PNG, JPG, JPEG, or GIF'}), 400
                
                # Check file size (max 5MB)
                photo.seek(0, os.SEEK_END)
                size = photo.tell()
                photo.seek(0)
                
                if size > 5 * 1024 * 1024:  # 5MB
                    return jsonify({'success': False, 'message': 'Profile photo too large (max 5MB)'}), 400
                
                # Save photo
                filename = secure_filename(f"prof_{int(datetime.utcnow().timestamp())}_{photo.filename}")
                photo_path = os.path.join('static', 'uploads', 'profiles', filename)
                photo.save(photo_path)
                profile_photo = filename
        
        # Create user
        user = User(
            username=username,
            email=email,
            first_name=first_name,
            last_name=last_name,
            phone=phone,
            role='professional',
            profile_pic=profile_photo,
            bio=bio
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
        
        # Parse specializations
        try:
            specializations_list = json.loads(specializations) if specializations else []
        except:
            specializations_list = [s.strip() for s in specializations.split(',') if s.strip()]
        
        # Create professional profile
        professional = Professional(
            user_id=user.id,
            professional_type=professional_type,
            license_number=license_number,
            years_experience=int(years_experience) if years_experience else 0,
            specialization=json.dumps(specializations_list),
            session_fee=float(session_fee),
            documents=json.dumps(documents),
            is_verified=False  # Requires admin approval
        )
        
        db.session.add(professional)
        db.session.commit()
        
        # Log activity
        log_activity(user.id, 'REGISTER', f'Professional registered', 'user', user.id)
        
        # Notify admins
        admins = User.query.filter_by(role='superadmin').all()
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
            'redirect': url_for('auth.login')
        })
        
    except Exception as e:
        db.session.rollback()
        print(f"Professional registration error: {str(e)}")
        return jsonify({'success': False, 'message': 'Registration failed. Please try again.'}), 500

# ========== COMPLETE ORGANIZATION REGISTRATION WITH ALL ROLES ==========
@auth_bp.route('/api/register/organization', methods=['POST'])
def api_register_organization():
    """Register organization with all roles (Admin, Manager, HR, Supervisor, Employee)"""
    try:
        data = request.json
        
        # Verify registration code for organization creation
        if data.get('role') == 'admin' and data.get('registration_code') != 'Papai123':
            return jsonify({'success': False, 'message': 'Invalid registration code'}), 400
        
        # Validate required fields based on role
        if data.get('role') == 'admin':
            required = ['company_name', 'registration_number', 'employee_count', 'email', 'phone', 'password']
            for field in required:
                if not data.get(field):
                    return jsonify({'success': False, 'message': f'{field} is required'}), 400
        else:
            # For non-admin roles, they need organization code
            required = ['first_name', 'last_name', 'email', 'phone', 'password', 'organization_code', 'role']
            for field in required:
                if not data.get(field):
                    return jsonify({'success': False, 'message': f'{field} is required'}), 400
        
        # Get role - default to employee if not specified
        role = data.get('role', 'employee')
        valid_roles = ['admin', 'manager', 'hr', 'supervisor', 'employee']
        
        if role not in valid_roles:
            return jsonify({'success': False, 'message': 'Invalid role selected'}), 400
        
        # Map frontend roles to database roles
        role_mapping = {
            'admin': 'organization_admin',
            'manager': 'org_manager',
            'hr': 'org_hr',
            'supervisor': 'org_supervisor',
            'employee': 'org_employee'
        }
        
        db_role = role_mapping[role]
        
        # Validate email
        if not validate_email(data['email']):
            return jsonify({'success': False, 'message': 'Invalid email format'}), 400
        
        # Validate phone
        if not validate_phone(data['phone']):
            return jsonify({'success': False, 'message': 'Invalid phone number format'}), 400
        
        # Check if user exists
        if User.query.filter_by(email=data['email']).first():
            return jsonify({'success': False, 'message': 'Email already registered'}), 400
        
        # For admin role, check registration number uniqueness
        if role == 'admin':
            if Organization.query.filter_by(registration_number=data['registration_number']).first():
                return jsonify({'success': False, 'message': 'This registration number is already registered'}), 400
        
        # Create username
        base_username = data.get('username') or data['email'].split('@')[0]
        username = base_username
        counter = 1
        while User.query.filter_by(username=username).first():
            username = f"{base_username}{counter}"
            counter += 1
        
        # Get name from data
        first_name = data.get('first_name', '')
        last_name = data.get('last_name', '')
        
        # For admin role, use contact_person if provided
        if role == 'admin' and not first_name and data.get('contact_person'):
            name_parts = data['contact_person'].strip().split()
            first_name = name_parts[0] if name_parts else 'Organization'
            last_name = ' '.join(name_parts[1:]) if len(name_parts) > 1 else 'Admin'
        
        # Create user
        user = User(
            username=username,
            email=data['email'],
            first_name=first_name,
            last_name=last_name,
            phone=data['phone'],
            role=db_role,
            is_active=True,
            is_verified=True if role != 'employee' else False  # Employees may need verification
        )
        user.set_password(data['password'])
        
        db.session.add(user)
        db.session.flush()
        
        # Set permissions based on role
        permissions = {}
        if role == 'admin':
            permissions = {
                'can_manage_all': True,
                'can_manage_departments': True,
                'can_view_all_employees': True,
                'can_manage_settings': True,
                'can_generate_reports': True,
                'can_manage_roles': True
            }
        elif role == 'manager':
            permissions = {
                'can_view_department_stats': True,
                'can_manage_team': True,
                'can_view_employees': True,
                'can_view_reports': True,
                'can_manage_schedules': True
            }
        elif role == 'hr':
            permissions = {
                'can_view_wellness_metrics': True,
                'can_view_risk_data': True,
                'can_generate_reports': True,
                'can_view_employees': True,
                'can_manage_wellness_programs': True
            }
        elif role == 'supervisor':
            permissions = {
                'can_view_team': True,
                'can_view_department_only': True,
                'can_view_employee_wellness': True,
                'can_recommend_assessments': True
            }
        else:  # employee
            permissions = {
                'can_take_assessments': True,
                'can_view_own_results': True,
                'can_chat_with_professionals': True,
                'can_view_recommendations': True,
                'can_use_ai_chat': True,
                'can_view_professionals': True
            }
        
        user.permissions = json.dumps(permissions)
        
        # Handle organization association
        organization_id = None
        employee_code = None
        
        if role == 'admin':
            # Generate employee registration code
            employee_code = secrets.token_hex(4).upper()
            while Organization.query.filter_by(employee_registration_code=employee_code).first():
                employee_code = secrets.token_hex(4).upper()
            
            # Create organization
            organization = Organization(
                user_id=user.id,
                company_name=data['company_name'],
                registration_number=data['registration_number'],
                industry=data.get('industry', ''),
                company_size=int(data['employee_count']),
                employee_registration_code=employee_code,
                anonymize_employee_data=True
            )
            db.session.add(organization)
            db.session.flush()
            organization_id = organization.id
            
            # If departments are provided, create them
            if data.get('departments'):
                depts = data.get('departments', '').split(',')
                for dept_name in depts:
                    if dept_name.strip():
                        dept = Department(
                            organization_id=organization.id,
                            name=dept_name.strip()
                        )
                        db.session.add(dept)
            
            message = f'Organization registered successfully! Your employee registration code is: {employee_code}'
            
        else:
            # For non-admin roles, they need an organization code
            org_code = data.get('organization_code')
            if not org_code:
                return jsonify({'success': False, 'message': 'Organization code required'}), 400
            
            org = Organization.query.filter_by(employee_registration_code=org_code).first()
            if not org:
                return jsonify({'success': False, 'message': 'Invalid organization code'}), 400
            
            organization_id = org.id
            
            # Create client/employee profile
            client = Client(
                user_id=user.id,
                organization_id=org.id,
                department=data.get('department', ''),
                employee_id=data.get('employee_id', ''),
                hide_profile=True
            )
            db.session.add(client)
            
            # Update organization stats
            org.total_employees += 1
            
            # If department head, update department
            if role == 'supervisor' and data.get('department'):
                dept = Department.query.filter_by(
                    organization_id=org.id,
                    name=data['department']
                ).first()
                if dept:
                    dept.head_id = user.id
            
            message = f'Registration successful! You are now registered as a {role.replace("_", " ").title()} with {org.company_name}.'
        
        db.session.commit()
        
        # Log activity
        log_activity(user.id, 'REGISTER', f'Registered as {role}', 'user', user.id)
        
        # Create welcome notification
        welcome_message = f"Welcome to Elmed Wellmind!"
        if role == 'employee':
            welcome_message = f"Welcome! You can take assessments, chat with professionals, and track your wellness journey."
        elif role == 'admin':
            welcome_message = f"Welcome! Your organization has been created. Share the employee code with your team."
        
        create_notification(
            user.id,
            'Welcome!',
            welcome_message,
            'success',
            '/dashboard'
        )
        
        return jsonify({
            'success': True,
            'message': message,
            'employee_code': employee_code,
            'role': role,
            'redirect': url_for('auth.login')
        })
        
    except Exception as e:
        db.session.rollback()
        print(f"Organization registration error: {str(e)}")
        return jsonify({'success': False, 'message': 'Registration failed. Please try again.'}), 500

# API: Register department head (legacy, kept for compatibility)
@auth_bp.route('/api/register/department-head', methods=['POST'])
def api_register_department_head():
    """Register as department head (legacy)"""
    try:
        data = request.json
        
        # Validate required fields
        required_fields = ['first_name', 'last_name', 'email', 'password', 'organization_code', 'department']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'success': False, 'message': f'{field.replace("_", " ").title()} is required'}), 400
        
        # Validate email
        if not validate_email(data['email']):
            return jsonify({'success': False, 'message': 'Invalid email format'}), 400
        
        # Validate password
        if len(data['password']) < 8:
            return jsonify({'success': False, 'message': 'Password must be at least 8 characters'}), 400
        
        # Find organization by code
        organization = Organization.query.filter_by(employee_registration_code=data['organization_code']).first()
        if not organization:
            return jsonify({'success': False, 'message': 'Invalid organization code'}), 400
        
        # Find or create department
        department = Department.query.filter_by(
            organization_id=organization.id,
            name=data['department']
        ).first()
        
        if not department:
            department = Department(
                organization_id=organization.id,
                name=data['department']
            )
            db.session.add(department)
            db.session.flush()
        
        # Check if department already has a head
        if department.head_id:
            return jsonify({'success': False, 'message': 'This department already has a head'}), 400
        
        # Check if user exists
        if User.query.filter_by(email=data['email']).first():
            return jsonify({'success': False, 'message': 'Email already registered'}), 400
        
        # Create username
        base_username = data['email'].split('@')[0]
        username = base_username
        counter = 1
        while User.query.filter_by(username=username).first():
            username = f"{base_username}{counter}"
            counter += 1
        
        # Create user
        user = User(
            username=username,
            email=data['email'],
            first_name=data['first_name'],
            last_name=data['last_name'],
            phone=data.get('phone', ''),
            role='org_supervisor',  # Map to supervisor role
            permissions=json.dumps({
                'can_view_team': True,
                'can_view_department_only': True,
                'can_view_employee_wellness': True,
                'can_recommend_assessments': True
            })
        )
        user.set_password(data['password'])
        
        db.session.add(user)
        db.session.flush()
        
        # Create client profile
        client = Client(
            user_id=user.id,
            organization_id=organization.id,
            department=department.name,
            hide_profile=True
        )
        db.session.add(client)
        
        # Update department stats
        organization.total_employees += 1
        department.employee_count += 1
        
        db.session.commit()
        
        # Log activity
        log_activity(user.id, 'REGISTER', f'Department head registered for {department.name}')
        
        # Notify organization admin
        create_notification(
            organization.user_id,
            'New Department Head Registered',
            f'{user.get_full_name()} has registered as head of {department.name}.',
            'info',
            '/organization/departments'
        )
        
        return jsonify({
            'success': True,
            'message': 'Registration successful! You can now log in as department head.',
            'redirect': url_for('auth.login')
        })
        
    except Exception as e:
        db.session.rollback()
        print(f"Department head registration error: {str(e)}")
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
        'phone_verified': current_user.phone_verified,
        'profile_pic': current_user.profile_pic,
        'bio': current_user.bio,
        'created_at': current_user.created_at.isoformat() if current_user.created_at else None,
        'last_login': current_user.last_login.isoformat() if current_user.last_login else None,
        'last_active': current_user.last_active.isoformat() if current_user.last_active else None
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
            'average_rating': prof.average_rating,
            'total_sessions': prof.total_sessions,
            'specializations': prof.get_specializations()
        }
    
    elif current_user.role in ['organization_admin', 'org_manager', 'org_hr', 'org_supervisor'] and current_user.organization_profile:
        org = current_user.organization_profile
        user_data['organization'] = {
            'id': org.id,
            'company_name': org.company_name,
            'employee_code': org.employee_registration_code,
            'total_employees': org.total_employees,
            'active_this_month': org.active_this_month,
            'average_wellness_score': org.average_wellness_score
        }
    
    elif current_user.role == 'org_supervisor' and current_user.client_profile:
        client = current_user.client_profile
        if client.department:
            user_data['department'] = {
                'name': client.department
            }
    
    elif current_user.role in ['client', 'org_employee'] and current_user.client_profile:
        client = current_user.client_profile
        user_data['client'] = {
            'id': client.id,
            'organization_id': client.organization_id,
            'department': client.department,
            'wellness_score': client.wellness_score,
            'risk_level': client.risk_level,
            'hide_profile': client.hide_profile
        }
    
    # Add permissions
    user_data['permissions'] = json.loads(current_user.permissions) if current_user.permissions else {}
    
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
        
        if not token or not new_password:
            return jsonify({'success': False, 'message': 'Token and password required'}), 400
        
        if len(new_password) < 8:
            return jsonify({'success': False, 'message': 'Password must be at least 8 characters'}), 400
        
        user = User.query.filter_by(reset_token=token).first()
        if not user or not user.verify_reset_token(token):
            return jsonify({'success': False, 'message': 'Invalid or expired token'}), 400
        
        user.set_password(new_password)
        user.reset_token = None
        user.reset_token_expiry = None
        db.session.commit()
        
        log_activity(user.id, 'PASSWORD_RESET', 'Password reset completed')
        
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
            'role': current_user.role,
            'name': current_user.get_full_name()
        })
    return jsonify({'authenticated': False})

# API: Verify email
@auth_bp.route('/api/verify-email/<token>', methods=['GET'])
def api_verify_email(token):
    """Verify email with token"""
    user = User.query.filter_by(verification_token=token).first()
    if not user:
        return jsonify({'success': False, 'message': 'Invalid verification token'}), 400
    
    user.email_verified = True
    user.verification_token = None
    db.session.commit()
    
    log_activity(user.id, 'EMAIL_VERIFIED', 'Email verified')
    
    return jsonify({'success': True, 'message': 'Email verified successfully'})
