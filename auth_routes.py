# auth_routes.py - Updated Registration
from flask import Blueprint, render_template, request, jsonify, redirect, url_for
from flask_login import login_user, logout_user, login_required, current_user
from models import db, User, Client, Professional, Organization, Department, Notification
from datetime import datetime
import secrets
import json

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')

# Registration page with role selection
@auth_bp.route('/register')
def register_page():
    return render_template('auth/register.html')

# Get started redirect
@auth_bp.route('/get-started')
def get_started():
    return redirect(url_for('auth.register_page'))

# API: Register client
@auth_bp.route('/api/register/client', methods=['POST'])
def api_register_client():
    try:
        data = request.json
        
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
        
        return jsonify({
            'success': True,
            'message': 'Registration successful! Please login.',
            'redirect': url_for('auth.login_page')
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500

# API: Register professional
@auth_bp.route('/api/register/professional', methods=['POST'])
def api_register_professional():
    try:
        data = request.json
        
        # Create user
        user = User(
            username=data['email'].split('@')[0] + secrets.token_hex(2),
            email=data['email'],
            first_name=data['first_name'],
            last_name=data['last_name'],
            phone=data['phone'],
            role='professional'
        )
        user.set_password(data['password'])
        
        db.session.add(user)
        db.session.flush()
        
        # Handle file uploads (documents)
        documents = []
        if 'documents' in request.files:
            files = request.files.getlist('documents')
            for file in files:
                # Save file and add path to documents list
                filename = f"prof_{user.id}_{file.filename}"
                file.save(f"uploads/documents/{filename}")
                documents.append(filename)
        
        # Create professional profile
        professional = Professional(
            user_id=user.id,
            professional_type=data['professional_type'],
            license_number=data['license_number'],
            years_experience=data.get('years_experience', 0),
            specialization=json.dumps(data.get('specializations', [])),
            session_fee=data['session_fee'],
            documents=json.dumps(documents)
        )
        
        db.session.add(professional)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Registration successful! Your account will be verified by admin.',
            'redirect': url_for('auth.login_page')
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500

# API: Register organization
@auth_bp.route('/api/register/organization', methods=['POST'])
def api_register_organization():
    try:
        data = request.json
        
        # Verify registration code
        if data.get('registration_code') != 'Papai123':
            return jsonify({'success': False, 'message': 'Invalid registration code'}), 400
        
        # Create user
        user = User(
            username=data['email'].split('@')[0] + secrets.token_hex(2),
            email=data['email'],
            first_name=data['contact_person'],
            last_name='',
            phone=data['phone'],
            role='organization'
        )
        user.set_password(data['password'])
        
        db.session.add(user)
        db.session.flush()
        
        # Create organization profile
        organization = Organization(
            user_id=user.id,
            company_name=data['company_name'],
            registration_number=data['registration_number'],
            industry=data.get('industry', ''),
            company_size=data['employee_count']
        )
        
        # Generate employee registration code
        organization.generate_employee_code()
        
        db.session.add(organization)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Organization registered successfully!',
            'employee_code': organization.employee_registration_code,
            'redirect': url_for('auth.login_page')
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500