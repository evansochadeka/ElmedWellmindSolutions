@organization_bp.route('/api/dashboard/data')
@login_required
def api_dashboard_data():
    """Get organization dashboard data"""
    org = Organization.query.filter_by(user_id=current_user.id).first()
    if not org:
        return jsonify({'error': 'Organization not found'}), 404
    
    employees = Client.query.filter_by(organization_id=org.id).all()
    
    # Calculate stats
    total_employees = len(employees)
    active_today = sum(1 for e in employees if e.user.last_active and 
                      e.user.last_active.date() == datetime.now().date())
    
    total_sessions = Session.query.filter(
        Session.client_id.in_([e.id for e in employees])
    ).count()
    
    avg_wellness = sum(e.wellness_score for e in employees) / total_employees if total_employees > 0 else 0
    
    # Department breakdown
    departments = Department.query.filter_by(organization_id=org.id).all()
    dept_data = []
    for dept in departments:
        dept_employees = [e for e in employees if e.department_id == dept.id]
        dept_data.append({
            'id': dept.id,
            'name': dept.name,
            'employee_count': len(dept_employees),
            'avg_wellness': sum(e.wellness_score for e in dept_employees) / len(dept_employees) if dept_employees else 0,
            'high_risk': sum(1 for e in dept_employees if e.risk_level == 'high'),
            'active_today': sum(1 for e in dept_employees if e.user.last_active and 
                               e.user.last_active.date() == datetime.now().date())
        })
    
    return jsonify({
        'stats': {
            'total_employees': total_employees,
            'active_today': active_today,
            'total_sessions': total_sessions,
            'avg_wellness': avg_wellness
        },
        'departments': dept_data,
        'employees': [{
            'id': e.id,
            'department': e.department.name if e.department else None,
            'wellness_score': e.wellness_score,
            'risk_level': e.risk_level,
            'last_active': e.user.last_active.isoformat() if e.user.last_active else None,
            'sessions': len(e.sessions)
        } for e in employees]
    })

@organization_bp.route('/api/professionals')
@login_required
def api_professionals():
    """Get all verified professionals"""
    professionals = Professional.query.filter_by(is_verified=True).all()
    
    return jsonify([{
        'id': p.id,
        'name': p.user.get_full_name(),
        'profile_pic': p.user.profile_pic,
        'type': p.professional_type,
        'specializations': p.get_specializations(),
        'years_experience': p.years_experience,
        'license_number': p.license_number,
        'average_rating': p.average_rating,
        'total_sessions': p.total_sessions,
        'response_rate': p.response_rate,
        'review_count': Review.query.filter_by(reviewee_id=p.user_id).count()
    } for p in professionals])

@organization_bp.route('/api/submit-complaint', methods=['POST'])
@login_required
def api_submit_complaint():
    """Submit complaint about a professional"""
    data = request.json
    org = Organization.query.filter_by(user_id=current_user.id).first()
    
    complaint = Complaint(
        organization_id=org.id,
        professional_id=data['professional_id'],
        type=data['type'],
        description=data['description'],
        status='pending'
    )
    db.session.add(complaint)
    
    # Notify superadmin
    admins = User.query.filter_by(role='superadmin').all()
    for admin in admins:
        notification = Notification(
            user_id=admin.id,
            title='New Complaint',
            message=f'Complaint from {org.company_name} against professional',
            notification_type='warning',
            link='/superadmin/complaints'
        )
        db.session.add(notification)
    
    db.session.commit()
    
    return jsonify({'success': True})

@organization_bp.route('/api/complaints')
@login_required
def api_complaints():
    """Get organization's complaints"""
    org = Organization.query.filter_by(user_id=current_user.id).first()
    
    complaints = Complaint.query.filter_by(organization_id=org.id)\
                    .order_by(Complaint.created_at.desc()).all()
    
    return jsonify([{
        'id': c.id,
        'professional_name': c.professional.user.get_full_name(),
        'type': c.type,
        'description': c.description,
        'status': c.status,
        'response': c.response,
        'created_at': c.created_at.isoformat()
    } for c in complaints])
