# auth_routes.py - Enhanced with proper error messages
from flask import Blueprint, render_template, request, jsonify, redirect, url_for, session
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.utils import secure_filename
from models import db, User, Client, Professional, Organization, Department, DepartmentHead, Notification, ActivityLog, WellnessAssessment
from datetime import datetime, timedelta
import secrets
import os
import json
import re

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')

# Validation functions
EMAIL_REGEX = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
PHONE_REGEX = re.compile(r'^(\+254|0)[0-9]{9}$')
PASSWORD_REGEX = re.compile(r'^(?=.*[A-Za-z])(?=.*\d)(?=.*[@$!%*#?&])[A-Za-z\d@$!%*#?&]{8,}$')

def validate_email(email):
    return bool(EMAIL_REGEX.match(email))

def validate_phone(phone):
    return bool(PHONE_REGEX.match(phone))

def validate_password(password):
    return bool(PASSWORD_REGEX.match(password))

def save_uploaded_file(file, user_id, file_type):
    """Save uploaded file and return filename"""
    if file and file.filename:
        # Validate file type
        allowed_extensions = {'pdf', 'jpg', 'jpeg', 'png', 'doc', 'docx'}
        ext = file.filename.rsplit('.', 1)[1].lower() if '.' in file.filename else ''
        
        if ext not in allowed_extensions:
            return None, "File type not allowed"
        
        # Check file size (max 5MB)
        file.seek(0, os.SEEK_END)
        size = file.tell()
        file.seek(0)
        
        if size > 5 * 1024 * 1024:  # 5MB
            return None, "File too large (max 5MB)"
        
        filename = secure_filename(f"{user_id}_{file_type}_{int(datetime.utcnow().timestamp())}.{ext}")
        file_path = os.path.join('static', 'uploads', file_type, filename)
        file.save(file_path)
        return filename, None
    return None, None

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

def log_activity(user_id, action, description=None, entity_type=None, entity_id=None, impersonated_by=None):
    """Log user activity"""
    log = ActivityLog(
        user_id=user_id,
        action=action,
        description=description,
        entity_type=entity_type,
        entity_id=entity_id,
        impersonated_by=impersonated_by,
        ip_address=request.remote_addr,
        user_agent=request.user_agent.string if request.user_agent else None
    )
    db.session.add(log)
    db.session.commit()

# Registration page
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

# API: Register client
@auth_bp.route('/api/register/client', methods=['POST'])
def api_register_client():
    try:
        data = request.json
        
        # Validate required fields
        required = ['first_name', 'last_name', 'email', 'password']
        for field in required:
            if not data.get(field):
                return jsonify({
                    'success': False,
                    'message': f'{field.replace("_", " ").title()} is required',
                    'field': field
                }), 400
        
        # Validate email
        if not validate_email(data['email']):
            return jsonify({
                'success': False,
                'message': 'Please enter a valid email address',
                'field': 'email'
            }), 400
        
        # Validate phone if provided
        if data.get('phone') and not validate_phone(data['phone']):
            return jsonify({
                'success': False,
                'message': 'Please enter a valid phone number (e.g., +254712345678 or 0712345678)',
                'field': 'phone'
            }), 400
        
        # Validate password strength
        if not validate_password(data['password']):
            return jsonify({
                'success': False,
                'message': 'Password must be at least 8 characters with at least one letter, one number, and one special character',
                'field': 'password'
            }), 400
        
        # Check if user exists
        if User.query.filter_by(email=data['email']).first():
            return jsonify({
                'success': False,
                'message': 'This email is already registered. Please login instead.',
                'field': 'email'
            }), 400
        
        # Check organization code if provided
        organization = None
        department = None
        if data.get('organization_code'):
            organization = Organization.query.filter_by(employee_registration_code=data['organization_code']).first()
            if not organization:
                return jsonify({
                    'success': False,
                    'message': 'Invalid organization code. Please check and try again.',
                    'field': 'organization_code'
                }), 400
            
            # Check if department exists or create it
            if data.get('department'):
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
        
        # Create username
        base_username = data['email'].split('@')[0]
        username = base_username
        counter = 1
        while User.query.filter_by(username=username).first():
            username = f"{base_username}{counter}"
            counter += 1
        
        # Determine role
        role = 'employee' if organization else 'client'
        
        # Create user
        user = User(
            username=username,
            email=data['email'],
            first_name=data['first_name'],
            last_name=data['last_name'],
            phone=data.get('phone', ''),
            role=role
        )
        user.set_password(data['password'])
        
        db.session.add(user)
        db.session.flush()
        
        # Create client profile
        client = Client(
            user_id=user.id,
            brief_issue=data.get('brief_issue', ''),
            emergency_contact=data.get('emergency_contact', ''),
            emergency_contact_name=data.get('emergency_contact_name', ''),
            organization_id=organization.id if organization else None,
            department_id=department.id if department else None,
            employee_id=data.get('employee_id', ''),
            hide_profile=True  # Default to hidden for privacy
        )
        
        db.session.add(client)
        
        # Update organization stats if applicable
        if organization:
            organization.total_employees += 1
            if department:
                department.employee_count += 1
        
        db.session.commit()
        
        # Log activity
        log_activity(user.id, 'REGISTER', f'{role.capitalize()} registered', 'user', user.id)
        
        # Create welcome notification
        welcome_message = "Thank you for registering"
        if role == 'employee':
            welcome_message = f"Welcome to {organization.company_name}'s wellness program. Your privacy is protected - your employer will only see anonymized data."
        
        create_notification(
            user.id,
            'Welcome to Elmed Wellmind!',
            welcome_message,
            'success',
            '/dashboard'
        )
        
        return jsonify({
            'success': True,
            'message': 'Registration successful! Please login to continue.',
            'redirect': url_for('auth.login')
        })
        
    except Exception as e:
        db.session.rollback()
        print(f"Client registration error: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'An error occurred during registration. Please try again.'
        }), 500

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
        required_fields = {
            'first_name': 'First name',
            'last_name': 'Last name',
            'email': 'Email address',
            'phone': 'Phone number',
            'professional_type': 'Professional type',
            'license_number': 'License number',
            'session_fee': 'Session fee',
            'password': 'Password'
        }
        
        for field, label in required_fields.items():
            value = locals().get(field)
            if not value:
                return jsonify({
                    'success': False,
                    'message': f'{label} is required',
                    'field': field
                }), 400
        
        # Validate email
        if not validate_email(email):
            return jsonify({
                'success': False,
                'message': 'Please enter a valid email address',
                'field': 'email'
            }), 400
        
        # Validate phone
        if not validate_phone(phone):
            return jsonify({
                'success': False,
                'message': 'Please enter a valid phone number (e.g., +254712345678)',
                'field': 'phone'
            }), 400
        
        # Validate password
        if not validate_password(password):
            return jsonify({
                'success': False,
                'message': 'Password must be at least 8 characters with at least one letter, one number, and one special character',
                'field': 'password'
            }), 400
        
        # Validate session fee
        try:
            fee = float(session_fee)
            if fee <= 0:
                raise ValueError()
        except:
            return jsonify({
                'success': False,
                'message': 'Please enter a valid session fee',
                'field': 'session_fee'
            }), 400
        
        # Check if user exists
        if User.query.filter_by(email=email).first():
            return jsonify({
                'success': False,
                'message': 'This email is already registered',
                'field': 'email'
            }), 400
        
        # Check license number uniqueness
        if Professional.query.filter_by(license_number=license_number).first():
            return jsonify({
                'success': False,
                'message': 'This license number is already registered',
                'field': 'license_number'
            }), 400
        
        # Create username
        base_username = email.split('@')[0]
        username = base_username
        counter = 1
        while User.query.filter_by(username=username).first():
            username = f"{base_username}{counter}"
            counter += 1
        
        # Create user
        user = User(
            username=username,
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
        upload_errors = []
        if 'documents' in request.files:
            files = request.files.getlist('documents')
            if not files or files[0].filename == '':
                return jsonify({
                    'success': False,
                    'message': 'Please upload your professional documents',
                    'field': 'documents'
                }), 400
            
            for file in files:
                if file and file.filename:
                    filename, error = save_uploaded_file(file, user.id, 'documents')
                    if error:
                        upload_errors.append(f"{file.filename}: {error}")
                    elif filename:
                        documents.append(filename)
        
        if upload_errors:
            return jsonify({
                'success': False,
                'message': 'File upload errors: ' + ', '.join(upload_errors),
                'field': 'documents'
            }), 400
        
        if not documents:
            return jsonify({
                'success': False,
                'message': 'Please upload at least one document',
                'field': 'documents'
            }), 400
        
        # Parse specializations
        try:
            specializations_list = json.loads(specializations) if specializations else []
            if not isinstance(specializations_list, list):
                specializations_list = [s.strip() for s in specializations.split(',') if s.strip()]
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
            is_verified=False
        )
        
        db.session.add(professional)
        db.session.commit()
        
        # Log activity
        log_activity(user.id, 'REGISTER', 'Professional registered', 'user', user.id)
        
        # Notify superadmins
        admins = User.query.filter_by(role='superadmin').all()
        for admin in admins:
            create_notification(
                admin.id,
                'New Professional Registration',
                f'{user.get_full_name()} has registered as a {professional_type}. Please verify their documents.',
                'info',
                '/admin/professionals'
            )
        
        return jsonify({
            'success': True,
            'message': 'Registration successful! Your account will be verified by our team within 24-48 hours. You will receive an email once verified.',
            'redirect': url_for('auth.login')
        })
        
    except Exception as e:
        db.session.rollback()
        print(f"Professional registration error: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'An error occurred during registration. Please try again.'
        }), 500

# API: Register organization
@auth_bp.route('/api/register/organization', methods=['POST'])
def api_register_organization():
    try:
        data = request.json
        
        # Verify registration code
        if data.get('registration_code') != 'Papai123':
            return jsonify({
                'success': False,
                'message': 'Invalid registration code. Please contact support.',
                'field': 'registration_code'
            }), 400
        
        # Validate required fields
        required_fields = {
            'company_name': 'Company name',
            'registration_number': 'Registration number',
            'employee_count': 'Number of employees',
            'contact_person': 'Contact person name',
            'email': 'Email address',
            'phone': 'Phone number',
            'password': 'Password'
        }
        
        for field, label in required_fields.items():
            if not data.get(field):
                return jsonify({
                    'success': False,
                    'message': f'{label} is required',
                    'field': field
                }), 400
        
        # Validate employee count
        try:
            emp_count = int(data['employee_count'])
            if emp_count <= 0:
                raise ValueError()
        except:
            return jsonify({
                'success': False,
                'message': 'Please enter a valid number of employees',
                'field': 'employee_count'
            }), 400
        
        # Validate email
        if not validate_email(data['email']):
            return jsonify({
                'success': False,
                'message': 'Please enter a valid email address',
                'field': 'email'
            }), 400
        
        # Validate phone
        if not validate_phone(data['phone']):
            return jsonify({
                'success': False,
                'message': 'Please enter a valid phone number (e.g., +254712345678)',
                'field': 'phone'
            }), 400
        
        # Validate password
        if not validate_password(data['password']):
            return jsonify({
                'success': False,
                'message': 'Password must be at least 8 characters with at least one letter, one number, and one special character',
                'field': 'password'
            }), 400
        
        # Check if user exists
        if User.query.filter_by(email=data['email']).first():
            return jsonify({
                'success': False,
                'message': 'This email is already registered',
                'field': 'email'
            }), 400
        
        # Check registration number uniqueness
        if Organization.query.filter_by(registration_number=data['registration_number']).first():
            return jsonify({
                'success': False,
                'message': 'This registration number is already registered',
                'field': 'registration_number'
            }), 400
        
        # Create username
        base_username = data['email'].split('@')[0]
        username = base_username
        counter = 1
        while User.query.filter_by(username=username).first():
            username = f"{base_username}{counter}"
            counter += 1
        
        # Parse contact person name
        name_parts = data['contact_person'].strip().split()
        first_name = name_parts[0] if name_parts else data['contact_person']
        last_name = ' '.join(name_parts[1:]) if len(name_parts) > 1 else ''
        
        # Create user (organization admin)
        user = User(
            username=username,
            email=data['email'],
            first_name=first_name,
            last_name=last_name,
            phone=data['phone'],
            role='organization_admin'
        )
        user.set_password(data['password'])
        
        db.session.add(user)
        db.session.flush()
        
        # Generate employee registration code
        employee_code = secrets.token_hex(4).upper()
        while Organization.query.filter_by(employee_registration_code=employee_code).first():
            employee_code = secrets.token_hex(4).upper()
        
        # Create organization profile
        organization = Organization(
            user_id=user.id,
            company_name=data['company_name'],
            registration_number=data['registration_number'],
            industry=data.get('industry', ''),
            company_size=emp_count,
            employee_registration_code=employee_code,
            anonymize_employee_data=True  # Default to anonymized
        )
        
        db.session.add(organization)
        db.session.commit()
        
        # Log activity
        log_activity(user.id, 'REGISTER', f'Organization registered: {data["company_name"]}', 'organization', organization.id)
        
        return jsonify({
            'success': True,
            'message': f'Organization registered successfully! Your employee registration code is: {employee_code}',
            'employee_code': employee_code,
            'redirect': url_for('auth.login')
        })
        
    except Exception as e:
        db.session.rollback()
        print(f"Organization registration error: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'An error occurred during registration. Please try again.'
        }), 500

# API: Register department head
@auth_bp.route('/api/register/department-head', methods=['POST'])
def api_register_department_head():
    """Register as department head (invited by organization admin)"""
    try:
        data = request.json
        
        # Validate required fields
        required_fields = ['first_name', 'last_name', 'email', 'password', 'organization_code', 'department']
        for field in required_fields:
            if not data.get(field):
                return jsonify({
                    'success': False,
                    'message': f'{field.replace("_", " ").title()} is required',
                    'field': field
                }), 400
        
        # Validate email
        if not validate_email(data['email']):
            return jsonify({
                'success': False,
                'message': 'Please enter a valid email address',
                'field': 'email'
            }), 400
        
        # Validate password
        if not validate_password(data['password']):
            return jsonify({
                'success': False,
                'message': 'Password must be at least 8 characters with at least one letter, one number, and one special character',
                'field': 'password'
            }), 400
        
        # Find organization by code
        organization = Organization.query.filter_by(employee_registration_code=data['organization_code']).first()
        if not organization:
            return jsonify({
                'success': False,
                'message': 'Invalid organization code',
                'field': 'organization_code'
            }), 400
        
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
            return jsonify({
                'success': False,
                'message': 'This department already has a head',
                'field': 'department'
            }), 400
        
        # Check if user exists
        if User.query.filter_by(email=data['email']).first():
            return jsonify({
                'success': False,
                'message': 'This email is already registered',
                'field': 'email'
            }), 400
        
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
            role='department_head'
        )
        user.set_password(data['password'])
        
        db.session.add(user)
        db.session.flush()
        
        # Create department head profile
        dept_head = DepartmentHead(
            user_id=user.id,
            organization_id=organization.id,
            department_id=department.id,
            can_view_department_data=True,
            can_suggest_tests=True,
            can_view_anonymized_only=True
        )
        
        db.session.add(dept_head)
        
        # Update department head reference
        department.head_id = dept_head.id
        
        db.session.commit()
        
        # Log activity
        log_activity(user.id, 'REGISTER', f'Department head registered for {department.name}', 'department_head', dept_head.id)
        
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
        return jsonify({
            'success': False,
            'message': 'An error occurred during registration. Please try again.'
        }), 500

# API: Login
@auth_bp.route('/api/login', methods=['POST'])
def api_login():
    try:
        data = request.json
        email = data.get('email')
        password = data.get('password')
        remember = data.get('remember', False)
        
        if not email or not password:
            return jsonify({
                'success': False,
                'message': 'Email and password are required'
            }), 400
        
        # Find user
        user = User.query.filter_by(email=email).first()
        
        if not user:
            return jsonify({
                'success': False,
                'message': 'No account found with this email'
            }), 401
        
        if not user.check_password(password):
            return jsonify({
                'success': False,
                'message': 'Incorrect password'
            }), 401
        
        if not user.is_active:
            return jsonify({
                'success': False,
                'message': 'This account has been deactivated. Please contact support.'
            }), 403
        
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
        elif user.role == 'organization_admin':
            redirect_url = url_for('organization.dashboard')
        elif user.role == 'department_head':
            redirect_url = url_for('department_head.dashboard')
        elif user.role == 'professional':
            redirect_url = url_for('professional.dashboard')
        else:
            redirect_url = url_for('client.dashboard')
        
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
        return jsonify({
            'success': False,
            'message': 'An error occurred during login. Please try again.'
        }), 500

# API: Logout
@auth_bp.route('/api/logout', methods=['POST'])
@login_required
def api_logout():
    """Logout user"""
    log_activity(current_user.id, 'LOGOUT', 'User logged out')
    logout_user()
    session.clear()
    return jsonify({'success': True, 'message': 'Logged out successfully'})

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
        'bio': current_user.bio,
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
    
    elif current_user.role in ['organization_admin', 'department_head'] and current_user.organization_profile:
        org = current_user.organization_profile
        user_data['organization'] = {
            'id': org.id,
            'company_name': org.company_name,
            'employee_code': org.employee_registration_code,
            'total_employees': org.total_employees,
            'anonymize_data': org.anonymize_employee_data
        }
        
        if current_user.role == 'department_head' and current_user.department_head_profile:
            dept_head = current_user.department_head_profile
            user_data['department'] = {
                'id': dept_head.department.id if dept_head.department else None,
                'name': dept_head.department.name if dept_head.department else None
            }
    
    elif current_user.role in ['client', 'employee'] and current_user.client_profile:
        client = current_user.client_profile
        user_data['client'] = {
            'id': client.id,
            'organization_id': client.organization_id,
            'department_id': client.department_id,
            'wellness_score': client.wellness_score,
            'risk_level': client.risk_level,
            'hide_profile': client.hide_profile
        }
    
    return jsonify(user_data)
# Add this to your auth_routes.py

@auth_bp.route('/api/register/organization', methods=['POST'])
def api_register_organization():
    """Register organization with role selection"""
    try:
        data = request.json
        
        # Verify registration code
        if data.get('registration_code') != 'Papai123':
            return jsonify({
                'success': False,
                'message': 'Invalid registration code. Please contact support.',
                'field': 'registration_code'
            }), 400
        
        # Validate required fields
        required_fields = {
            'company_name': 'Company name',
            'registration_number': 'Registration number',
            'employee_count': 'Number of employees',
            'contact_person': 'Contact person name',
            'email': 'Email address',
            'phone': 'Phone number',
            'password': 'Password',
            'role': 'Organization role'
        }
        
        for field, label in required_fields.items():
            if not data.get(field):
                return jsonify({
                    'success': False,
                    'message': f'{label} is required',
                    'field': field
                }), 400
        
        # Validate organization role
        valid_roles = ['manager', 'department_head', 'it_support', 'hr_manager']
        if data['role'] not in valid_roles:
            return jsonify({
                'success': False,
                'message': 'Invalid organization role selected',
                'field': 'role'
            }), 400
        
        # Validate employee count
        try:
            emp_count = int(data['employee_count'])
            if emp_count <= 0:
                raise ValueError()
        except:
            return jsonify({
                'success': False,
                'message': 'Please enter a valid number of employees',
                'field': 'employee_count'
            }), 400
        
        # Validate email
        if not validate_email(data['email']):
            return jsonify({
                'success': False,
                'message': 'Please enter a valid email address',
                'field': 'email'
            }), 400
        
        # Validate phone
        if not validate_phone(data['phone']):
            return jsonify({
                'success': False,
                'message': 'Please enter a valid phone number (e.g., +254712345678)',
                'field': 'phone'
            }), 400
        
        # Validate password
        if not validate_password(data['password']):
            return jsonify({
                'success': False,
                'message': 'Password must be at least 8 characters with at least one letter, one number, and one special character',
                'field': 'password'
            }), 400
        
        # Check if user exists
        if User.query.filter_by(email=data['email']).first():
            return jsonify({
                'success': False,
                'message': 'This email is already registered',
                'field': 'email'
            }), 400
        
        # Check registration number uniqueness
        if Organization.query.filter_by(registration_number=data['registration_number']).first():
            return jsonify({
                'success': False,
                'message': 'This registration number is already registered',
                'field': 'registration_number'
            }), 400
        
        # Create username
        base_username = data['email'].split('@')[0]
        username = base_username
        counter = 1
        while User.query.filter_by(username=username).first():
            username = f"{base_username}{counter}"
            counter += 1
        
        # Parse contact person name
        name_parts = data['contact_person'].strip().split()
        first_name = name_parts[0] if name_parts else data['contact_person']
        last_name = ' '.join(name_parts[1:]) if len(name_parts) > 1 else ''
        
        # Map organization role to system role
        role_mapping = {
            'manager': 'org_manager',
            'department_head': 'org_dept_head',
            'it_support': 'org_it',
            'hr_manager': 'org_hr'
        }
        
        system_role = role_mapping.get(data['role'], 'org_employee')
        
        # Create user with specific organization role
        user = User(
            username=username,
            email=data['email'],
            first_name=first_name,
            last_name=last_name,
            phone=data['phone'],
            role=system_role,
            permissions=json.dumps({
                'can_view_analytics': data['role'] in ['manager', 'hr_manager'],
                'can_view_department': data['role'] in ['department_head', 'manager'],
                'can_reset_passwords': data['role'] == 'it_support',
                'can_manage_users': data['role'] in ['manager', 'hr_manager'],
                'view_anonymized_only': True  # Always true for privacy
            })
        )
        user.set_password(data['password'])
        
        db.session.add(user)
        db.session.flush()
        
        # Generate employee registration code
        employee_code = secrets.token_hex(4).upper()
        while Organization.query.filter_by(employee_registration_code=employee_code).first():
            employee_code = secrets.token_hex(4).upper()
        
        # Create organization profile
        organization = Organization(
            user_id=user.id,
            company_name=data['company_name'],
            registration_number=data['registration_number'],
            industry=data.get('industry', ''),
            company_size=emp_count,
            employee_registration_code=employee_code,
            anonymize_employee_data=True,
            org_role=data['role']
        )
        
        db.session.add(organization)
        
        # If department head, create department
        if data['role'] == 'department_head' and data.get('department_name'):
            department = Department(
                organization_id=organization.id,
                name=data['department_name'],
                description=data.get('department_description', '')
            )
            db.session.add(department)
            db.session.flush()
            
            # Link department head
            organization.department_id = department.id
        
        db.session.commit()
        
        # Log activity
        log_activity(user.id, 'REGISTER', f'Organization registered as {data["role"]}', 'organization', organization.id)
        
        role_display = {
            'manager': 'Organization Manager',
            'department_head': 'Department Head',
            'it_support': 'IT Support',
            'hr_manager': 'HR Manager'
        }
        
        return jsonify({
            'success': True,
            'message': f'{role_display[data["role"]]} registration successful! Your employee registration code is: {employee_code}',
            'employee_code': employee_code,
            'role': data['role'],
            'redirect': url_for('auth.login')
        })
        
    except Exception as e:
        db.session.rollback()
        print(f"Organization registration error: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'An error occurred during registration. Please try again.'
        }), 500
# Add to auth_routes.py

@auth_bp.route('/api/register/employee', methods=['POST'])
def api_register_employee():
    """Register as employee using organization code"""
    try:
        data = request.json
        
        # Validate required fields
        required_fields = ['first_name', 'last_name', 'email', 'password', 'organization_code']
        for field in required_fields:
            if not data.get(field):
                return jsonify({
                    'success': False,
                    'message': f'{field.replace("_", " ").title()} is required',
                    'field': field
                }), 400
        
        # Validate email
        if not validate_email(data['email']):
            return jsonify({
                'success': False,
                'message': 'Please enter a valid email address',
                'field': 'email'
            }), 400
        
        # Validate password
        if not validate_password(data['password']):
            return jsonify({
                'success': False,
                'message': 'Password must be at least 8 characters with at least one letter, one number, and one special character',
                'field': 'password'
            }), 400
        
        # Find organization by code
        organization = Organization.query.filter_by(employee_registration_code=data['organization_code']).first()
        if not organization:
            return jsonify({
                'success': False,
                'message': 'Invalid organization code. Please check and try again.',
                'field': 'organization_code'
            }), 400
        
        # Check if user exists
        if User.query.filter_by(email=data['email']).first():
            return jsonify({
                'success': False,
                'message': 'This email is already registered',
                'field': 'email'
            }), 400
        
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
            role='org_employee',
            permissions=json.dumps({
                'can_take_tests': True,
                'can_view_own_results': True,
                'can_book_sessions': True,
                'can_consult_specialists': True
            })
        )
        user.set_password(data['password'])
        
        db.session.add(user)
        db.session.flush()
        
        # Find or create department
        department_id = None
        if data.get('department'):
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
            department_id = department.id
        
        # Create client/employee profile
        employee = Client(
            user_id=user.id,
            organization_id=organization.id,
            department_id=department_id,
            employee_id=data.get('employee_id', ''),
            brief_issue=data.get('brief_issue', ''),
            hide_profile=True,  # Always hide for privacy
            wellness_score=0.0,
            risk_level='low'
        )
        
        db.session.add(employee)
        
        # Update organization stats
        organization.total_employees += 1
        if department_id:
            dept = Department.query.get(department_id)
            dept.employee_count += 1
        
        db.session.commit()
        
        # Log activity
        log_activity(user.id, 'REGISTER', f'Employee registered for {organization.company_name}', 'employee', employee.id)
        
        return jsonify({
            'success': True,
            'message': f'Registration successful! Welcome to {organization.company_name}.',
            'redirect': url_for('auth.login')
        })
        
    except Exception as e:
        db.session.rollback()
        print(f"Employee registration error: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'An error occurred during registration. Please try again.'
        }), 500
