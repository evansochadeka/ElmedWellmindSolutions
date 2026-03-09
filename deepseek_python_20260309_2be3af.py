# professional_routes.py
from flask import Blueprint, render_template, jsonify, request
from flask_login import login_required, current_user
from models import db, Professional, Session, SessionRequest, Webinar, Notification
from datetime import datetime, timedelta

professional_bp = Blueprint('professional', __name__, url_prefix='/professional')

@professional_bp.route('/dashboard')
@login_required
def dashboard():
    if not current_user.is_professional:
        return redirect(url_for('main.index'))
    return render_template('professional/dashboard.html')

@professional_bp.route('/api/dashboard/stats')
@login_required
def api_dashboard_stats():
    if not current_user.is_professional:
        return jsonify({'error': 'Unauthorized'}), 403
    
    professional = current_user.professional_profile
    
   