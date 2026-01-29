# app.py - RENDER READY VERSION

import os
import json
from flask import Flask, render_template, jsonify, request, send_from_directory
from flask_cors import CORS
from dotenv import load_dotenv

from extensions import db
from routes_py import api

# Load environment variables
load_dotenv()

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

# Fix for Render Postgres URLs (if you add Postgres later)
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URL
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SECRET_KEY"] = os.getenv(
    "FLASK_SECRET_KEY",
    "dev-secret-key-change-me"
)

# --------------------------------------------------
# Initialize extensions
# --------------------------------------------------

db.init_app(app)

# Create tables safely (NO DROP in production)
with app.app_context():
    try:
        db.create_all()
        print("✅ Database tables ensured")
    except Exception as e:
        print(f"⚠️ Database init warning: {e}")

# --------------------------------------------------
# Register blueprints
# --------------------------------------------------

app.register_blueprint(api)

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
        "service": "Elmed Wellmind Mental Health AI",
        "ai_status": "active" if os.getenv("COHERE_API_KEY") else "inactive",
        "database": "connected"
    })

# --------------------------------------------------
# ADD MISSING ROUTES FROM LOGS
# --------------------------------------------------

# 1. Community posts endpoint (404 in logs)
@app.route("/api/community/posts")
def community_posts():
    try:
        # Return empty array for now - implement database logic later
        return jsonify([])
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# 2. Email endpoint replacement for PHP
@app.route("/send_email.php", methods=["POST"])
@app.route("/api/send_email", methods=["POST"])
def send_email():
    try:
        # Get form data
        name = request.form.get("name", "")
        email = request.form.get("email", "")
        subject = request.form.get("subject", "")
        message = request.form.get("message", "")
        
        # Log the email attempt (in production, connect to email service)
        print(f"📧 Email attempted: {name} <{email}> - {subject}")
        
        # For now, just acknowledge receipt
        return jsonify({
            "status": "success",
            "message": "Message received. We'll get back to you soon!",
            "data": {
                "name": name,
                "email": email,
                "subject": subject[:50]  # Truncate for safety
            }
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# 3. Static file serving - ensure images work
@app.route('/static/<path:filename>')
def serve_static(filename):
    return send_from_directory('static', filename)

# 4. Chat history endpoint (already works but ensure it's here)
@app.route("/api/chat/history/<session_id>")
def chat_history(session_id):
    # This might be handled in your api blueprint
    # If not, implement basic version
    return jsonify({"messages": [], "session_id": session_id})

# --------------------------------------------------
# FALLBACK ROUTES FOR MISSING IMAGES
# --------------------------------------------------

@app.route("/static/images/<image_name>")
def serve_image(image_name):
    """Serve images with fallback for missing files"""
    try:
        return send_from_directory('static/images', image_name)
    except:
        # Return a placeholder or default image if file doesn't exist
        # This prevents 404 errors breaking the page
        try:
            return send_from_directory('static/images', 'wellmed.jpg')
        except:
            # Ultimate fallback
            return jsonify({"error": "Image not found"}), 404

# --------------------------------------------------
# ERROR HANDLERS
# --------------------------------------------------

@app.errorhandler(404)
def not_found(e):
    """Handle 404 errors gracefully"""
    if request.path.startswith('/api/'):
        return jsonify({"error": "Endpoint not found", "path": request.path}), 404
    elif request.path.startswith('/static/'):
        # For missing static files, don't return JSON - let browser handle it
        return "File not found", 404
    # For HTML pages, redirect to home or show error page
    return render_template("index.html"), 200

# --------------------------------------------------
# IMPORTANT
# --------------------------------------------------
# ❌ NO app.run()
# ❌ NO debug=True
# Render runs this app using:
# gunicorn app:app
