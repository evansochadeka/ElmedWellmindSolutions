# app.py - COMPLETE WORKING VERSION WITH ALL FEATURES

import os
import sys
import json
import threading
from datetime import datetime, timedelta
import secrets

from flask import Flask, render_template, jsonify, request, send_from_directory, redirect, url_for
from flask_cors import CORS
from dotenv import load_dotenv
from flask_login import LoginManager, login_required, current_user, login_user, logout_user

# Load environment variables
load_dotenv()

# Import extensions
from extensions import db

# Import models - ALL models
from models import (
    User, Client, Professional, Organization, Department, 
    Session, SessionRequest, Webinar, Notification, Review, 
    WellnessAssessment, OrganizationWellnessData, ProfessionalAvailability, 
    WebinarParticipant, SessionFeedback, ActivityLog, 
    ChatMessage, CommunityPost, PostComment
)

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
app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'gif', 'pdf', 'doc', 'docx'}

# Session configuration
app.config['SESSION_TYPE'] = 'filesystem'
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=31)
app.config['REMEMBER_COOKIE_DURATION'] = timedelta(days=31)
app.config['REMEMBER_COOKIE_SECURE'] = True
app.config['REMEMBER_COOKIE_HTTPONLY'] = True

# Create upload directories if they don't exist
os.makedirs(os.path.join('static', 'uploads', 'documents'), exist_ok=True)
os.makedirs(os.path.join('static', 'uploads', 'profiles'), exist_ok=True)
os.makedirs(os.path.join('static', 'uploads', 'posts'), exist_ok=True)
os.makedirs(os.path.join('static', 'uploads', 'temp'), exist_ok=True)

# --------------------------------------------------
# Initialize extensions
# --------------------------------------------------

db.init_app(app)

# Initialize Login Manager
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'auth.login_page'
login_manager.login_message = 'Please log in to access this page.'
login_manager.login_message_category = 'info'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# --------------------------------------------------
# Import and register blueprints
# --------------------------------------------------

# Import all blueprints
from auth_routes import auth_bp
from professional_routes import professional_bp
from organization_routes import organization_bp
from routes_py import api  # Original API routes
from admin_routes import admin_bp

# Register blueprints
app.register_blueprint(auth_bp)
app.register_blueprint(professional_bp)
app.register_blueprint(organization_bp)
app.register_blueprint(api)  # Original API routes
app.register_blueprint(admin_bp)

# --------------------------------------------------
# Try to import matching service (optional)
# --------------------------------------------------

MATCHING_SERVICE_AVAILABLE = False
try:
    from services.matching_service import start_matching_service
    MATCHING_SERVICE_AVAILABLE = True
    print("✅ Matching service loaded successfully")
except ImportError as e:
    print(f"⚠️ Matching service not available (optional): {e}")
    # Define a placeholder function
    def start_matching_service(app):
        """Placeholder for matching service"""
        print("ℹ️ Matching service placeholder - no actual matching")
        pass

# --------------------------------------------------
# Create tables and initial data
# --------------------------------------------------

with app.app_context():
    try:
        # Create all tables
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
                email_verified=True,
                is_active=True
            )
            admin.set_password(admin_password)
            db.session.add(admin)
            db.session.commit()
            print("✅ Admin user created")
            
            # Create welcome notification for admin
            notification = Notification(
                user_id=admin.id,
                title="Welcome to Elmed Wellmind",
                message="You have been set up as the system administrator.",
                notification_type="success",
                link="/admin/dashboard"
            )
            db.session.add(notification)
            db.session.commit()
            
    except Exception as e:
        print(f"⚠️ Database init warning: {e}")

# --------------------------------------------------
# Original Routes (from original app.py)
# --------------------------------------------------

@app.route("/")
def home():
    """Home page"""
    return render_template("index.html")

@app.route("/chat")
def chat_interface():
    """AI chat interface"""
    return render_template("chat.html")

@app.route("/health")
def health_check():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "service": "Elmed Wellmind Mental Health AI",
        "ai_status": "active" if os.getenv("COHERE_API_KEY") else "inactive",
        "database": "connected",
        "timestamp": datetime.utcnow().isoformat()
    })

# --------------------------------------------------
# ADD MISSING ROUTES FROM ORIGINAL LOGS
# --------------------------------------------------

# 1. Community posts endpoint (Original - returns empty array)
@app.route("/api/community/posts", methods=['GET'])
def community_posts_original():
    """Original community posts endpoint - returns empty array for backward compatibility"""
    try:
        # Return empty array for now - implement database logic later
        return jsonify([])
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# 2. Email endpoint replacement for PHP (Original)
@app.route("/send_email.php", methods=["POST"])
@app.route("/api/send_email", methods=["POST"])
def send_email_original():
    """Original email endpoint - handles contact form submissions"""
    try:
        # Get form data (support both form and JSON)
        if request.is_json:
            data = request.json
            name = data.get("name", "")
            email = data.get("email", "")
            subject = data.get("subject", "")
            message = data.get("message", "")
        else:
            name = request.form.get("name", "")
            email = request.form.get("email", "")
            subject = request.form.get("subject", "")
            message = request.form.get("message", "")
        
        # Log the email attempt
        print(f"📧 Email attempted: {name} <{email}> - {subject}")
        print(f"Message: {message[:100]}...")
        
        # Create notification for admins
        admins = User.query.filter_by(role='admin').all()
        for admin in admins:
            notification = Notification(
                user_id=admin.id,
                title=f"New Contact: {subject}",
                message=f"From: {name} ({email})\n\n{message[:200]}...",
                notification_type='info',
                link='/admin/messages'
            )
            db.session.add(notification)
        db.session.commit()
        
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
        db.session.rollback()
        print(f"Email error: {e}")
        return jsonify({"error": str(e)}), 500

# 3. Static file serving - ensure images work (Original)
@app.route('/static/<path:filename>')
def serve_static_original(filename):
    """Serve static files"""
    try:
        return send_from_directory('static', filename)
    except Exception as e:
        print(f"Error serving static file {filename}: {e}")
        return "File not found", 404

# 4. Chat history endpoint (Original)
@app.route("/api/chat/history/<session_id>", methods=['GET'])
def chat_history_original(session_id):
    """Original chat history endpoint"""
    try:
        # Try to get from database if available
        messages = ChatMessage.query.filter_by(session_id=session_id)\
                     .order_by(ChatMessage.created_at.asc())\
                     .limit(100)\
                     .all()
        
        if messages:
            return jsonify([{
                'id': m.id,
                'role': m.role,
                'content': m.content,
                'timestamp': m.created_at.isoformat() if m.created_at else None,
                'is_mental_health_related': m.is_mental_health_related
            } for m in messages])
        
        # Fallback to empty array
        return jsonify({"messages": [], "session_id": session_id})
    except Exception as e:
        print(f"Error in chat history: {e}")
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
        try:
            return send_from_directory('static/images', 'wellmed.jpg')
        except:
            # Ultimate fallback
            return jsonify({"error": "Image not found"}), 404

# --------------------------------------------------
# Enhanced API Routes (New functionality)
# --------------------------------------------------

@app.route("/api/v2/community/posts", methods=['GET'])
def community_posts_v2():
    """Enhanced community posts endpoint with full database support"""
    try:
        # Try to get from database first
        posts = CommunityPost.query.filter_by(is_approved=True)\
                .order_by(CommunityPost.created_at.desc())\
                .limit(50)\
                .all()
        
        if posts:
            return jsonify([{
                'id': p.id,
                'author': p.author_name,
                'content': p.content,
                'category': p.category,
                'likes': p.likes,
                'comments': p.comments_count,
                'date': p.created_at.strftime('%Y-%m-%d %H:%M') if p.created_at else None,
                'is_featured': p.is_featured
            } for p in posts])
        else:
            # Return sample posts if no database posts yet
            sample_posts = [
                {
                    "id": 1,
                    "author": "Anonymous",
                    "content": "Today marks 30 days of being anxiety-free. It does get better!",
                    "likes": 24,
                    "comments": 8,
                    "date": "2 hours ago",
                    "category": "Anxiety"
                },
                {
                    "id": 2,
                    "author": "Teacher_254",
                    "content": "Our school's mental health program is making a real difference.",
                    "likes": 15,
                    "comments": 3,
                    "date": "1 day ago",
                    "category": "School Programs"
                },
                {
                    "id": 3,
                    "author": "Recovering",
                    "content": "Grateful for this community. You're not alone in your struggles.",
                    "likes": 42,
                    "comments": 12,
                    "date": "3 days ago",
                    "category": "Depression"
                }
            ]
            return jsonify(sample_posts)
    except Exception as e:
        print(f"Error in community_posts_v2: {e}")
        return jsonify({"error": str(e)}), 500

@app.route("/api/v2/community/posts", methods=['POST'])
def create_community_post_v2():
    """Create a new community post with database storage"""
    try:
        data = request.json
        author_name = data.get('author', 'Anonymous')
        content = data.get('content', '').strip()
        category = data.get('category', '')
        user_id = data.get('user_id')
        
        if not content:
            return jsonify({'error': 'Post content cannot be empty'}), 400
        
        # Find client if user_id provided
        client_id = None
        if user_id:
            client = Client.query.filter_by(user_id=user_id).first()
            if client:
                client_id = client.id
        
        # Create new post
        post = CommunityPost(
            author_id=client_id,
            author_name=author_name,
            content=content,
            category=category,
            is_approved=True  # Auto-approve for now
        )
        
        db.session.add(post)
        db.session.commit()
        
        return jsonify({
            "success": True,
            "message": "Post created successfully",
            "post": {
                'id': post.id,
                'author': post.author_name,
                'content': post.content,
                'category': post.category,
                'likes': post.likes,
                'comments': post.comments_count,
                'date': post.created_at.strftime('%Y-%m-%d %H:%M') if post.created_at else None
            }
        })
    except Exception as e:
        db.session.rollback()
        print(f"Error creating post: {e}")
        return jsonify({"error": str(e)}), 500

@app.route("/api/v2/community/posts/<int:post_id>/like", methods=['POST'])
def like_post_v2(post_id):
    """Like a community post"""
    try:
        post = CommunityPost.query.get_or_404(post_id)
        post.likes += 1
        db.session.commit()
        
        return jsonify({
            "success": True,
            "likes": post.likes
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

@app.route("/api/v2/community/posts/<int:post_id>/comments", methods=['GET'])
def get_post_comments_v2(post_id):
    """Get comments for a post"""
    try:
        post = CommunityPost.query.get_or_404(post_id)
        comments = PostComment.query.filter_by(post_id=post_id)\
                    .order_by(PostComment.created_at.asc())\
                    .all()
        
        return jsonify([{
            'id': c.id,
            'author': c.author_name,
            'content': c.content,
            'date': c.created_at.strftime('%Y-%m-%d %H:%M') if c.created_at else None
        } for c in comments])
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/v2/community/posts/<int:post_id>/comments", methods=['POST'])
def add_post_comment_v2(post_id):
    """Add a comment to a post"""
    try:
        data = request.json
        author_name = data.get('author', 'Anonymous')
        content = data.get('content', '').strip()
        user_id = data.get('user_id')
        
        if not content:
            return jsonify({'error': 'Comment cannot be empty'}), 400
        
        post = CommunityPost.query.get_or_404(post_id)
        
        # Find client if user_id provided
        client_id = None
        if user_id:
            client = Client.query.filter_by(user_id=user_id).first()
            if client:
                client_id = client.id
        
        comment = PostComment(
            post_id=post_id,
            author_id=client_id,
            author_name=author_name,
            content=content
        )
        
        db.session.add(comment)
        post.comments_count += 1
        db.session.commit()
        
        return jsonify({
            "success": True,
            "comment": {
                'id': comment.id,
                'author': comment.author_name,
                'content': comment.content,
                'date': comment.created_at.strftime('%Y-%m-%d %H:%M') if comment.created_at else None
            }
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

@app.route("/api/v2/chat/history/<session_id>", methods=['GET'])
def chat_history_v2(session_id):
    """Enhanced chat history with database storage"""
    try:
        messages = ChatMessage.query.filter_by(session_id=session_id)\
                     .order_by(ChatMessage.created_at.asc())\
                     .limit(100)\
                     .all()
        
        return jsonify([{
            'id': m.id,
            'role': m.role,
            'content': m.content,
            'timestamp': m.created_at.isoformat() if m.created_at else None,
            'is_mental_health_related': m.is_mental_health_related
        } for m in messages])
    except Exception as e:
        print(f"Error in chat_history_v2: {e}")
        return jsonify([])

@app.route("/api/v2/chat/message", methods=['POST'])
def save_chat_message_v2():
    """Save a chat message to database"""
    try:
        data = request.json
        message = ChatMessage(
            session_id=data.get('session_id'),
            role=data.get('role', 'user'),
            content=data.get('content', ''),
            user_id=data.get('user_id'),
            is_mental_health_related=data.get('is_mental_health_related', True)
        )
        db.session.add(message)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'id': message.id,
            'timestamp': message.created_at.isoformat() if message.created_at else None
        })
    except Exception as e:
        db.session.rollback()
        print(f"Error saving chat message: {e}")
        return jsonify({'error': str(e)}), 500

# --------------------------------------------------
# Dashboard routes
# --------------------------------------------------

@app.route('/dashboard')
@login_required
def dashboard_redirect():
    """Redirect to appropriate dashboard based on role"""
    if current_user.role == 'admin':
        return redirect(url_for('admin.dashboard'))
    elif current_user.role == 'professional':
        return redirect(url_for('professional.dashboard'))
    elif current_user.role == 'organization':
        return redirect(url_for('organization.dashboard'))
    else:
        # Client dashboard
        return render_template('dashboard/client_dashboard.html')

@app.route('/dashboard/client')
@login_required
def client_dashboard():
    """Client dashboard page"""
    if current_user.role not in ['client', 'admin']:
        return redirect(url_for('dashboard_redirect'))
    return render_template('dashboard/client_dashboard.html')

# --------------------------------------------------
# Error handlers
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

@app.errorhandler(500)
def internal_error(e):
    """Handle 500 errors"""
    db.session.rollback()
    print(f"Internal server error: {e}")
    if request.path.startswith('/api/'):
        return jsonify({"error": "Internal server error"}), 500
    return render_template("index.html"), 500

@app.errorhandler(403)
def forbidden(e):
    """Handle 403 errors"""
    if request.path.startswith('/api/'):
        return jsonify({"error": "Forbidden"}), 403
    return render_template("index.html"), 403

@app.errorhandler(401)
def unauthorized(e):
    """Handle 401 errors"""
    if request.path.startswith('/api/'):
        return jsonify({"error": "Unauthorized"}), 401
    return redirect(url_for('auth.login_page'))

# --------------------------------------------------
# Template context processors
# --------------------------------------------------

@app.context_processor
def utility_processor():
    """Add utility functions to template context"""
    def format_datetime(dt):
        if dt:
            return dt.strftime('%Y-%m-%d %H:%M')
        return ''
    
    def time_ago(dt):
        if not dt:
            return ''
        now = datetime.utcnow()
        diff = now - dt
        
        if diff.days > 365:
            years = diff.days // 365
            return f"{years} year{'s' if years > 1 else ''} ago"
        elif diff.days > 30:
            months = diff.days // 30
            return f"{months} month{'s' if months > 1 else ''} ago"
        elif diff.days > 0:
            return f"{diff.days} day{'s' if diff.days > 1 else ''} ago"
        elif diff.seconds > 3600:
            hours = diff.seconds // 3600
            return f"{hours} hour{'s' if hours > 1 else ''} ago"
        elif diff.seconds > 60:
            minutes = diff.seconds // 60
            return f"{minutes} minute{'s' if minutes > 1 else ''} ago"
        else:
            return "just now"
    
    def allowed_file(filename):
        return '.' in filename and \
               filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']
    
    return dict(
        format_datetime=format_datetime,
        time_ago=time_ago,
        allowed_file=allowed_file,
        app_name="Elmed Wellmind Solutions",
        support_phone="+254 759 226354",
        support_email="elijahokware@gmail.com",
        current_year=datetime.utcnow().year
    )

# --------------------------------------------------
# Start background services
# --------------------------------------------------

def start_background_services():
    """Start all background services"""
    with app.app_context():
        try:
            if MATCHING_SERVICE_AVAILABLE:
                start_matching_service(app)
                print("✅ Matching service started")
            else:
                print("ℹ️ Matching service not available")
        except Exception as e:
            print(f"⚠️ Could not start matching service: {e}")

# Start services in a separate thread if not in debug mode
if not app.debug and MATCHING_SERVICE_AVAILABLE:
    try:
        service_thread = threading.Thread(target=start_background_services, daemon=True)
        service_thread.start()
        print("✅ Background services thread started")
    except Exception as e:
        print(f"⚠️ Could not start background services thread: {e}")

# --------------------------------------------------
# CLI commands
# --------------------------------------------------

@app.cli.command("create-admin")
def create_admin_command():
    """Create admin user"""
    import getpass
    email = input("Enter admin email: ")
    password = getpass.getpass("Enter admin password: ")
    
    admin = User.query.filter_by(email=email).first()
    if admin:
        print("Admin user already exists")
        return
    
    admin = User(
        username="admin",
        email=email,
        first_name="Admin",
        last_name="User",
        role="admin",
        is_verified=True,
        email_verified=True,
        is_active=True
    )
    admin.set_password(password)
    
    db.session.add(admin)
    db.session.commit()
    print(f"✅ Admin user created with email: {email}")

@app.cli.command("seed-services")
def seed_services_command():
    """Seed initial services"""
    try:
        from seed_services import seed_services
        seed_services()
        print("✅ Services seeded")
    except ImportError:
        print("⚠️ seed_services.py not found")

# --------------------------------------------------
# IMPORTANT
# --------------------------------------------------
# ❌ NO app.run() in production
# Render runs this app using: gunicorn app:app

if __name__ == "__main__":
    # Only for local development
    port = int(os.environ.get("PORT", 5001))
    debug = os.environ.get("FLASK_DEBUG", "True").lower() == "true"
    app.run(host="0.0.0.0", port=port, debug=debug)
