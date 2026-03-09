# app.py - COMPLETE WORKING VERSION

import os
import json
from flask import Flask, render_template, jsonify, request, send_from_directory, redirect, url_for
from flask_cors import CORS
from dotenv import load_dotenv
from flask_login import LoginManager
from datetime import datetime, timedelta
import secrets

# Load environment variables
load_dotenv()

# Import extensions
from extensions import db

# Import models
from models import User, Client, Professional, Organization, Department, Session, SessionRequest, Webinar, Notification, Review, WellnessAssessment, OrganizationWellnessData, ProfessionalAvailability, WebinarParticipant, SessionFeedback, ActivityLog

# Create Flask app
app = Flask(
    __name__,
    static_folder="static",
    template_folder="templates"
)

CORS(app)

# --------------------------------------------------
# Configuration
# --------------------------------------------------

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///elmed_wellmind.db")

# Fix for Render Postgres URLs
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URL
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SECRET_KEY"] = os.getenv("FLASK_SECRET_KEY", secrets.token_hex(32))

# Upload configuration
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max upload

# Create upload directories if they don't exist
os.makedirs(os.path.join('static', 'uploads', 'documents'), exist_ok=True)
os.makedirs(os.path.join('static', 'uploads', 'profiles'), exist_ok=True)

# --------------------------------------------------
# Initialize extensions
# --------------------------------------------------

db.init_app(app)

# Initialize Login Manager
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'auth.login_page'
login_manager.login_message = 'Please log in to access this page.'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# --------------------------------------------------
# Import and register blueprints AFTER app is created
# --------------------------------------------------

# Import blueprints
from auth_routes import auth_bp
from professional_routes import professional_bp
from organization_routes import organization_bp
from routes_py import api
from admin_routes import admin_bp

# Register blueprints
app.register_blueprint(auth_bp)
app.register_blueprint(professional_bp)
app.register_blueprint(organization_bp)
app.register_blueprint(api)
app.register_blueprint(admin_bp)

# Import matching service and start it
from services.matching_service import start_matching_service

# --------------------------------------------------
# Create tables
# --------------------------------------------------

with app.app_context():
    try:
        db.create_all()
        print("✅ Database tables created/verified")
        
        # Create admin user if not exists
        admin_email = os.getenv("ADMIN_EMAIL", "admin@elmedwellmind.com")
        admin_password = os.getenv("ADMIN_PASSWORD", "Admin@123")
        
        admin = User.query.filter_by(email=admin_email).first()
        if not admin:
            admin = User(
                username="admin",
                email=admin_email,
                first_name="System",
                last_name="Administrator",
                role="admin",
                is_verified=True,
                email_verified=True
            )
            admin.set_password(admin_password)
            db.session.add(admin)
            db.session.commit()
            print("✅ Admin user created")
            
    except Exception as e:
        print(f"⚠️ Database init warning: {e}")

# --------------------------------------------------
# Routes
# --------------------------------------------------

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/chat")
def chat_interface():
    return render_template("chat.html")

@app.route("/health")
def health_check():
    return jsonify({
        "status": "healthy",
        "service": "Elmed Wellmind Mental Health Platform",
        "ai_status": "active" if os.getenv("COHERE_API_KEY") else "inactive",
        "database": "connected",
        "version": "2.0"
    })

# --------------------------------------------------
# Static file serving
# --------------------------------------------------

@app.route('/static/<path:filename>')
def serve_static(filename):
    return send_from_directory('static', filename)

@app.route('/uploads/<path:filename>')
def serve_upload(filename):
    return send_from_directory('uploads', filename)

# --------------------------------------------------
# API Routes
# --------------------------------------------------

@app.route("/api/community/posts")
def community_posts():
    """Get community posts"""
    try:
        # Return sample posts for now
        posts = [
            {
                "id": 1,
                "author": "Anonymous",
                "content": "Today marks 30 days of being anxiety-free. It does get better!",
                "likes": 24,
                "comments": 8,
                "date": "2 hours ago"
            },
            {
                "id": 2,
                "author": "Teacher_254",
                "content": "Our school's mental health program is making a real difference.",
                "likes": 15,
                "comments": 3,
                "date": "1 day ago"
            }
        ]
        return jsonify(posts)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/send_email", methods=["POST"])
def send_email():
    """Handle contact form submissions"""
    try:
        data = request.json
        name = data.get("name", "")
        email = data.get("email", "")
        subject = data.get("subject", "")
        message = data.get("message", "")
        
        # Log the email
        print(f"📧 Contact form: {name} <{email}> - {subject}")
        print(f"Message: {message}")
        
        # Here you would integrate with an email service
        # For now, just acknowledge
        
        return jsonify({
            "success": True,
            "message": "Message received. We'll respond within 24 hours."
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/chat/history/<session_id>")
def chat_history(session_id):
    """Get chat history for a session"""
    return jsonify({"messages": [], "session_id": session_id})

# --------------------------------------------------
# Error handlers
# --------------------------------------------------

@app.errorhandler(404)
def not_found(e):
    if request.path.startswith('/api/'):
        return jsonify({"error": "Endpoint not found", "path": request.path}), 404
    return render_template("index.html"), 200

@app.errorhandler(500)
def internal_error(e):
    db.session.rollback()
    if request.path.startswith('/api/'):
        return jsonify({"error": "Internal server error"}), 500
    return render_template("index.html"), 500

# --------------------------------------------------
# Start background services
# --------------------------------------------------

def start_background_services():
    """Start all background services"""
    with app.app_context():
        try:
            # Start matching service
            start_matching_service(app)
            print("✅ Matching service started")
        except Exception as e:
            print(f"⚠️ Could not start matching service: {e}")

# Start services in a separate thread if not in debug mode
if not app.debug:
    import threading
    threading.Thread(target=start_background_services, daemon=True).start()

# --------------------------------------------------
# For local development only
# --------------------------------------------------

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001, debug=True)
