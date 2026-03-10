# assessment_routes.py
from flask import Blueprint, render_template, jsonify, request, redirect, url_for
from flask_login import login_required, current_user
from models import db, WellnessAssessment, Client, Organization, Department, Notification
from datetime import datetime
import json

assessment_bp = Blueprint('assessment', __name__, url_prefix='/assessment')

# Scoring guidelines
SECTION_WEIGHTS = {
    'stress': 10,
    'burnout': 8,
    'anxiety': 8,
    'mood': 8,
    'performance': 8,
    'environment': 8
}

REVERSE_SCORED_QUESTIONS = [35, 36, 38, 39, 41, 42, 43, 44, 46, 47, 49, 50]

@assessment_bp.route('/take')
@login_required
def take_assessment():
    """Take the wellness assessment"""
    return render_template('assessment/take_assessment.html')

@assessment_bp.route('/api/submit', methods=['POST'])
@login_required
def submit_assessment():
    """Submit assessment responses and calculate scores"""
    try:
        data = request.json
        responses = data.get('responses', {})
        
        # Get client profile
        client = Client.query.filter_by(user_id=current_user.id).first()
        if not client:
            return jsonify({'success': False, 'message': 'Client profile not found'}), 404
        
        # Calculate section scores
        scores = calculate_scores(responses)
        
        # Determine risk level
        risk_level = determine_risk_level(scores)
        
        # Generate recommendations
        recommendations = generate_recommendations(scores, responses)
        
        # Create assessment record
        assessment = WellnessAssessment(
            client_id=client.id,
            responses=json.dumps(responses),
            overall_score=scores['overall'],
            anxiety_score=scores['anxiety'],
            depression_score=scores['mood'],  # Using mood as depression indicator
            stress_score=scores['stress'],
            sleep_score=scores.get('sleep', 0),
            work_stress_score=scores['stress'],
            relationship_score=scores.get('relationship', 0),
            risk_level=risk_level,
            recommendations=json.dumps(recommendations)
        )
        
        db.session.add(assessment)
        
        # Update client stats
        client.assessment_count += 1
        client.last_assessment = datetime.utcnow()
        client.wellness_score = (client.wellness_score * (client.assessment_count - 1) + scores['overall']) / client.assessment_count
        client.risk_level = risk_level
        
        db.session.commit()
        
        # Notify department head if high risk
        if risk_level in ['high', 'critical'] and client.department_id:
            department = Department.query.get(client.department_id)
            if department and department.head_id:
                notification = Notification(
                    user_id=department.head.user_id,
                    title='High Risk Employee Alert',
                    message=f'An employee in {department.name} has scored high risk on wellness assessment.',
                    notification_type='warning',
                    link='/department-head/dashboard'
                )
                db.session.add(notification)
                db.session.commit()
        
        return jsonify({
            'success': True,
            'scores': scores,
            'risk_level': risk_level,
            'recommendations': recommendations,
            'redirect': url_for('assessment.results', assessment_id=assessment.id)
        })
        
    except Exception as e:
        db.session.rollback()
        print(f"Assessment submission error: {str(e)}")
        return jsonify({'success': False, 'message': 'Failed to submit assessment'}), 500

@assessment_bp.route('/results/<int:assessment_id>')
@login_required
def results(assessment_id):
    """View assessment results"""
    assessment = WellnessAssessment.query.get_or_404(assessment_id)
    # Verify ownership
    client = Client.query.filter_by(user_id=current_user.id).first()
    if assessment.client_id != client.id:
        return redirect(url_for('main.index'))
    
    return render_template('assessment/results.html', assessment=assessment)

@assessment_bp.route('/api/history')
@login_required
def get_history():
    """Get assessment history for current user"""
    client = Client.query.filter_by(user_id=current_user.id).first()
    if not client:
        return jsonify([])
    
    assessments = WellnessAssessment.query.filter_by(client_id=client.id)\
                    .order_by(WellnessAssessment.created_at.desc())\
                    .all()
    
    return jsonify([{
        'id': a.id,
        'date': a.created_at.strftime('%Y-%m-%d'),
        'overall_score': a.overall_score,
        'risk_level': a.risk_level,
        'stress_score': a.stress_score,
        'anxiety_score': a.anxiety_score,
        'mood_score': a.depression_score
    } for a in assessments])

def calculate_scores(responses):
    """Calculate section scores from responses"""
    sections = {
        'stress': list(range(1, 11)),
        'burnout': list(range(11, 19)),
        'anxiety': list(range(19, 27)),
        'mood': list(range(27, 35)),
        'performance': list(range(35, 43)),
        'environment': list(range(43, 51))
    }
    
    section_scores = {}
    total_raw = 0
    total_questions = 0
    
    for section, questions in sections.items():
        section_total = 0
        section_count = 0
        
        for q_num in questions:
            response_key = f"q{q_num}"
            if response_key in responses:
                value = int(responses[response_key])
                
                # Reverse score if needed
                if q_num in REVERSE_SCORED_QUESTIONS:
                    value = 4 - value
                
                section_total += value
                section_count += 1
                total_raw += value
                total_questions += 1
        
        # Calculate section score as percentage
        if section_count > 0:
            max_possible = section_count * 4
            section_scores[section] = round((section_total / max_possible) * 100, 1)
        else:
            section_scores[section] = 0
    
    # Calculate overall score
    if total_questions > 0:
        max_possible = total_questions * 4
        section_scores['overall'] = round((total_raw / max_possible) * 100, 1)
    else:
        section_scores['overall'] = 0
    
    return section_scores

def determine_risk_level(scores):
    """Determine risk level based on scores"""
    overall = scores['overall']
    
    if overall >= 75:
        return 'low'
    elif overall >= 50:
        return 'medium'
    elif overall >= 25:
        return 'high'
    else:
        return 'critical'

def generate_recommendations(scores, responses):
    """Generate personalized recommendations based on scores"""
    recommendations = []
    
    # Stress recommendations
    if scores['stress'] > 60:
        recommendations.append({
            'area': 'Stress Management',
            'severity': 'high' if scores['stress'] > 75 else 'medium',
            'tips': [
                'Practice deep breathing exercises (4-7-8 technique)',
                'Take regular short breaks during work hours',
                'Consider mindfulness meditation apps',
                'Speak with your supervisor about workload management'
            ]
        })
    
    # Burnout recommendations
    if scores['burnout'] > 60:
        recommendations.append({
            'area': 'Burnout Prevention',
            'severity': 'high' if scores['burnout'] > 75 else 'medium',
            'tips': [
                'Establish clear work-life boundaries',
                'Take your full lunch break away from your desk',
                'Use vacation days for mental rest',
                'Discuss role clarity with your manager'
            ]
        })
    
    # Anxiety recommendations
    if scores['anxiety'] > 50:
        recommendations.append({
            'area': 'Anxiety Management',
            'severity': 'high' if scores['anxiety'] > 70 else 'medium',
            'tips': [
                'Practice grounding techniques (5-4-3-2-1 method)',
                'Limit caffeine intake, especially after noon',
                'Break tasks into smaller, manageable steps',
                'Consider speaking with a counselor'
            ]
        })
    
    # Mood recommendations
    if scores['mood'] > 50:
        recommendations.append({
            'area': 'Mood & Motivation',
            'severity': 'high' if scores['mood'] > 70 else 'medium',
            'tips': [
                'Set small, achievable daily goals',
                'Connect with supportive colleagues',
                'Engage in physical activity during breaks',
                'Track positive moments in a gratitude journal'
            ]
        })
    
    # Performance recommendations
    if scores['performance'] > 60:
        recommendations.append({
            'area': 'Work Performance',
            'severity': 'high' if scores['performance'] > 75 else 'medium',
            'tips': [
                'Use time-blocking technique for tasks',
                'Prioritize tasks using Eisenhower matrix',
                'Minimize distractions (turn off notifications)',
                'Request regular feedback sessions'
            ]
        })
    
    # Environment recommendations
    if scores['environment'] > 60:
        recommendations.append({
            'area': 'Workplace Environment',
            'severity': 'high' if scores['environment'] > 75 else 'medium',
            'tips': [
                'Schedule a confidential chat with HR',
                'Build allyship with trusted colleagues',
                'Document any workplace concerns',
                'Explore employee resource groups'
            ]
        })
    
    # Add crisis resources for high risk
    if scores['overall'] < 40:
        recommendations.append({
            'area': 'Immediate Support',
            'severity': 'critical',
            'tips': [
                '🚨 24/7 Crisis Helpline: +254 759 226354',
                '📞 Emergency: 999 or 112',
                '🤝 Schedule a counseling session immediately',
                '💬 Chat with our AI assistant for instant support'
            ]
        })
    
    return recommendations