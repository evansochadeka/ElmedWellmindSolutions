# app.py - COMPLETE POSTGRESQL VERSION WITH ALL FEATURES - FIXED
import os
import sys
import json
import threading
from datetime import datetime, timedelta
import secrets

from flask import Flask, render_template, jsonify, request, send_from_directory, redirect, url_for, session
from flask_cors import CORS
from dotenv import load_dotenv
from flask_login import LoginManager, login_required, current_user, login_user, logout_user
from sqlalchemy import text

# Load environment variables
load_dotenv()

# Import extensions
from extensions import db

# Create Flask app
app = Flask(
    __name__,
    static_folder="static",
    template_folder="templates"
)

CORS(app)

# --------------------------------------------------
# PostgreSQL Configuration
# --------------------------------------------------
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://benfarming_db_user:2TBsWivCFfLXvDkop9WY62CNaxN9WmNl@dpg-d669k18gjchc73fli15g-a/benfarming_db")

# Fix for Render Postgres URLs
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URL
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SECRET_KEY"] = os.getenv("FLASK_SECRET_KEY", secrets.token_hex(32))

# PostgreSQL connection pool settings
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_size": 10,
    "pool_recycle": 300,
    "pool_pre_ping": True,
    "max_overflow": 20,
}

print("✅ PostgreSQL connection pool configured")
print(f"✅ Connecting to database: {DATABASE_URL.split('@')[0].split('://')[0]} database")

# Upload configuration
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024
app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'gif', 'pdf', 'doc', 'docx'}

# Session configuration
app.config['SESSION_TYPE'] = 'filesystem'
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=31)
app.config['REMEMBER_COOKIE_DURATION'] = timedelta(days=31)
app.config['REMEMBER_COOKIE_SECURE'] = True
app.config['REMEMBER_COOKIE_HTTPONLY'] = True

# Create directories
os.makedirs(os.path.join('static', 'uploads', 'documents'), exist_ok=True)
os.makedirs(os.path.join('static', 'uploads', 'profiles'), exist_ok=True)
os.makedirs(os.path.join('static', 'uploads', 'posts'), exist_ok=True)
os.makedirs(os.path.join('static', 'uploads', 'temp'), exist_ok=True)

# --------------------------------------------------
# Jinja2 Filters
# --------------------------------------------------

@app.template_filter('from_json')
def from_json_filter(value):
    """Convert JSON string to Python object"""
    try:
        if isinstance(value, str):
            return json.loads(value)
        return value
    except:
        return []

@app.template_filter('format_date')
def format_date_filter(date):
    """Format date nicely"""
    if date:
        return date.strftime('%B %d, %Y')
    return ''

# --------------------------------------------------
# Initialize extensions
# --------------------------------------------------

db.init_app(app)

# Initialize Login Manager
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'auth.login'
login_manager.login_message = 'Please log in to access this page.'
login_manager.login_message_category = 'info'

# Import models AFTER db is initialized
from models import *

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# --------------------------------------------------
# Safe import of blueprints with error handling
# --------------------------------------------------

# Dictionary to store blueprints that loaded successfully
loaded_blueprints = []

# Try to import each blueprint with error handling
try:
    from auth_routes import auth_bp
    app.register_blueprint(auth_bp)
    loaded_blueprints.append('auth')
    print("✅ Loaded auth blueprint")
except ImportError as e:
    print(f"⚠️ Could not load auth blueprint: {e}")

try:
    from professional_routes import professional_bp
    app.register_blueprint(professional_bp)
    loaded_blueprints.append('professional')
    print("✅ Loaded professional blueprint")
except ImportError as e:
    print(f"⚠️ Could not load professional blueprint: {e}")

try:
    from organization_routes import organization_bp
    app.register_blueprint(organization_bp)
    loaded_blueprints.append('organization')
    print("✅ Loaded organization blueprint")
except ImportError as e:
    print(f"⚠️ Could not load organization blueprint: {e}")

try:
    from routes_py import api
    app.register_blueprint(api)
    loaded_blueprints.append('api')
    print("✅ Loaded api blueprint")
except ImportError as e:
    print(f"⚠️ Could not load api blueprint: {e}")

try:
    from admin_routes import admin_bp
    app.register_blueprint(admin_bp)
    loaded_blueprints.append('admin')
    print("✅ Loaded admin blueprint")
except ImportError as e:
    print(f"⚠️ Could not load admin blueprint: {e}")

try:
    from superadmin_routes import superadmin_bp
    app.register_blueprint(superadmin_bp)
    loaded_blueprints.append('superadmin')
    print("✅ Loaded superadmin blueprint")
except ImportError as e:
    print(f"⚠️ Could not load superadmin blueprint: {e}")

try:
    from department_head_routes import dept_head_bp
    app.register_blueprint(dept_head_bp)
    loaded_blueprints.append('department_head')
    print("✅ Loaded department_head blueprint")
except ImportError as e:
    print(f"⚠️ Could not load department_head blueprint: {e}")

# employee_routes might not exist - handle gracefully
try:
    from employee_routes import employee_bp
    app.register_blueprint(employee_bp)
    loaded_blueprints.append('employee')
    print("✅ Loaded employee blueprint")
except ImportError as e:
    print(f"⚠️ Could not load employee blueprint (this is okay if not needed): {e}")
    # Define a placeholder function for employee dashboard redirect
    def employee_dashboard():
        return redirect(url_for('home'))

try:
    from chat_routes import chat_bp
    app.register_blueprint(chat_bp)
    loaded_blueprints.append('chat')
    print("✅ Loaded chat blueprint")
except ImportError as e:
    print(f"⚠️ Could not load chat blueprint: {e}")

try:
    from assessment_routes import assessment_bp
    app.register_blueprint(assessment_bp)
    loaded_blueprints.append('assessment')
    print("✅ Loaded assessment blueprint")
except ImportError as e:
    print(f"⚠️ Could not load assessment blueprint: {e}")

# --------------------------------------------------
# Try to import matching service
# --------------------------------------------------

MATCHING_SERVICE_AVAILABLE = False
try:
    from services.matching_service import start_matching_service
    MATCHING_SERVICE_AVAILABLE = True
    print("✅ Matching service loaded successfully")
except ImportError as e:
    print(f"⚠️ Matching service not available (optional): {e}")
    def start_matching_service(app):
        pass

# --------------------------------------------------
# Create tables and initial data - PostgreSQL Connection Test
# --------------------------------------------------

with app.app_context():
    try:
        # Test PostgreSQL connection
        result = db.session.execute(text('SELECT version()')).scalar()
        print(f"✅ Connected to PostgreSQL: {result[:100]}...")
        
        # Create all tables
        db.create_all()
        print("✅ Database tables created/verified")
        
        # Create superadmin if not exists
        superadmin_email = os.getenv("SUPERADMIN_EMAIL", "elijahokware@gmail.com")
        superadmin_password = os.getenv("SUPERADMIN_PASSWORD", "Pa$$w0rd")
        
        superadmin = User.query.filter_by(email=superadmin_email).first()
        if not superadmin:
            superadmin = User(
                username="elijahokware",
                email=superadmin_email,
                first_name="Elijah",
                last_name="Okware",
                role="superadmin",
                is_verified=True,
                email_verified=True,
                is_active=True,
                permissions=json.dumps({
                    'can_impersonate': True,
                    'can_manage_all': True,
                    'can_verify_professionals': True,
                    'can_manage_site_settings': True,
                    'can_promote_admins': True
                })
            )
            superadmin.set_password(superadmin_password)
            db.session.add(superadmin)
            db.session.commit()
            print("✅ Superadmin user created")
            print("   Email: elijahokware@gmail.com")
            print("   Password: Pa$$w0rd")
            
    except Exception as e:
        print(f"❌ PostgreSQL connection failed: {e}")
        print("Please check your DATABASE_URL environment variable")
        # Don't exit - let the app try to continue in case it's a temporary issue
        # sys.exit(1)

# --------------------------------------------------
# ORIGINAL ROUTES - ALL RETAINED
# --------------------------------------------------

@app.route("/")
def home():
    """Home page with assessment call-to-action"""
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
        "database_type": "postgresql",
        "blueprints_loaded": loaded_blueprints,
        "timestamp": datetime.utcnow().isoformat()
    })

# --------------------------------------------------
# ORIGINAL COMMUNITY POSTS ENDPOINT
# --------------------------------------------------

@app.route("/api/community/posts")
def community_posts():
    try:
        posts = CommunityPost.query.filter_by(is_approved=True)\
                .order_by(CommunityPost.created_at.desc())\
                .limit(50)\
                .all()
        
        if posts:
            return jsonify([post.to_dict() for post in posts])
        return jsonify([])
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/community/posts", methods=['POST'])
def create_community_post():
    try:
        data = request.json
        post = CommunityPost(
            author_name=data.get('author', 'Anonymous'),
            content=data.get('content', ''),
            category=data.get('category', '')
        )
        db.session.add(post)
        db.session.commit()
        return jsonify({"success": True, "post": post.to_dict()})
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

# --------------------------------------------------
# ORIGINAL EMAIL ENDPOINT
# --------------------------------------------------

@app.route("/send_email.php", methods=["POST"])
@app.route("/api/send_email", methods=["POST"])
def send_email():
    try:
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
        
        print(f"📧 Email attempted: {name} <{email}> - {subject}")
        
        return jsonify({
            "status": "success",
            "message": "Message received. We'll get back to you soon!",
            "data": {
                "name": name,
                "email": email,
                "subject": subject[:50]
            }
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# --------------------------------------------------
# CHAT HISTORY ENDPOINT
# --------------------------------------------------

@app.route("/api/chat/history/<session_id>")
def chat_history(session_id):
    try:
        messages = ChatMessage.query.filter_by(session_id=session_id)\
                     .order_by(ChatMessage.created_at.asc())\
                     .limit(100)\
                     .all()
        
        if messages:
            return jsonify([{
                'id': m.id,
                'role': m.role,
                'content': m.content,
                'timestamp': m.created_at.isoformat() if m.created_at else None
            } for m in messages])
        
        return jsonify({"messages": [], "session_id": session_id})
    except Exception as e:
        return jsonify({"messages": [], "session_id": session_id})

# --------------------------------------------------
# STATIC FILE SERVING
# --------------------------------------------------

@app.route('/static/<path:filename>')
def serve_static(filename):
    try:
        return send_from_directory('static', filename)
    except:
        return "File not found", 404

@app.route('/static/images/<path:filename>')
def serve_image(filename):
    try:
        return send_from_directory('static/images', filename)
    except:
        try:
            return send_from_directory('static/images', 'default.jpg')
        except:
            return "", 404

# --------------------------------------------------
# ASSESSMENT ROUTES
# --------------------------------------------------

@app.route('/assessment/take')
@login_required
def take_assessment():
    """Take the wellness assessment"""
    return render_template('assessment/take_assessment.html')

@app.route('/assessment/results/<int:assessment_id>')
@login_required
def assessment_results(assessment_id):
    """View assessment results"""
    assessment = WellnessAssessment.query.get_or_404(assessment_id)
    
    # Verify ownership
    client = Client.query.filter_by(user_id=current_user.id).first()
    if not client or assessment.client_id != client.id:
        if current_user.role not in ['superadmin', 'admin']:
            return redirect(url_for('home'))
    
    return render_template('assessment/results.html', assessment=assessment)

@app.route('/assessment/history')
@login_required
def assessment_history():
    """View assessment history"""
    client = Client.query.filter_by(user_id=current_user.id).first()
    if not client:
        return redirect(url_for('take_assessment'))
    
    assessments = WellnessAssessment.query.filter_by(client_id=client.id)\
                    .order_by(WellnessAssessment.created_at.desc())\
                    .all()
    
    return render_template('assessment/history.html', assessments=assessments)

# --------------------------------------------------
# DASHBOARD REDIRECT - With fallbacks for missing templates
# --------------------------------------------------

@app.route('/dashboard')
@login_required
def dashboard_redirect():
    """Redirect to appropriate dashboard based on role"""
    try:
        if current_user.role == 'superadmin':
            return redirect(url_for('superadmin.dashboard'))
        elif current_user.role == 'admin':
            return redirect(url_for('admin.dashboard'))
        elif current_user.role == 'professional':
            return redirect(url_for('professional.dashboard'))
        elif current_user.role == 'organization_admin':
            return redirect(url_for('organization.dashboard'))
        elif current_user.role == 'department_head':
            return redirect(url_for('dept_head.dashboard'))
        elif current_user.role == 'org_employee':
            # Check if employee blueprint is loaded
            if 'employee' in loaded_blueprints:
                return redirect(url_for('employee.dashboard'))
            else:
                return render_template('client/dashboard.html')
        else:
            return render_template('client/dashboard.html')
    except Exception as e:
        print(f"Dashboard redirect error: {e}")
        return render_template('index.html')

# --------------------------------------------------
# ERROR HANDLERS
# --------------------------------------------------

@app.errorhandler(404)
def not_found(e):
    if request.path.startswith('/api/'):
        return jsonify({"error": "Endpoint not found"}), 404
    return render_template("index.html"), 200

@app.errorhandler(500)
def internal_error(e):
    db.session.rollback()
    print(f"Internal server error: {e}")
    if request.path.startswith('/api/'):
        return jsonify({"error": "Internal server error"}), 500
    return render_template("index.html"), 500

# --------------------------------------------------
# TEMPLATE CONTEXT PROCESSORS
# --------------------------------------------------

@app.context_processor
def utility_processor():
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
    
    def get_risk_color(risk_level):
        colors = {
            'low': '#10B981',
            'medium': '#F59E0B',
            'high': '#EF4444',
            'critical': '#7F1D1D'
        }
        return colors.get(risk_level, '#6B7280')
    
    return dict(
        format_datetime=format_datetime,
        time_ago=time_ago,
        get_risk_color=get_risk_color,
        app_name="Elmed Wellmind Solutions",
        support_phone="+254 759 226354",
        support_email="elijahokware@gmail.com",
        current_year=datetime.utcnow().year
    )

# --------------------------------------------------
# CLI COMMANDS
# --------------------------------------------------

@app.cli.command("create-superadmin")
def create_superadmin_command():
    """Create superadmin user"""
    import getpass
    email = input("Enter superadmin email [elijahokware@gmail.com]: ") or "elijahokware@gmail.com"
    password = getpass.getpass("Enter superadmin password: ") or "Pa$$w0rd"
    
    admin = User.query.filter_by(email=email).first()
    if admin:
        admin.role = 'superadmin'
        print("Updated existing user to superadmin")
    else:
        admin = User(
            username=email.split('@')[0],
            email=email,
            first_name="Super",
            last_name="Admin",
            role="superadmin",
            is_verified=True,
            email_verified=True,
            is_active=True
        )
        admin.set_password(password)
        db.session.add(admin)
    
    db.session.commit()
    print(f"✅ Superadmin user created/updated with email: {email}")

# --------------------------------------------------
# START BACKGROUND SERVICES
# --------------------------------------------------

def start_background_services():
    with app.app_context():
        try:
            if MATCHING_SERVICE_AVAILABLE:
                start_matching_service(app)
                print("✅ Matching service started")
        except Exception as e:
            print(f"⚠️ Could not start matching service: {e}")

if not app.debug and MATCHING_SERVICE_AVAILABLE:
    try:
        service_thread = threading.Thread(target=start_background_services, daemon=True)
        service_thread.start()
        print("✅ Background services thread started")
    except Exception as e:
        print(f"⚠️ Could not start background services thread: {e}")

# --------------------------------------------------
# SIMPLE TEST ROUTE - Add this temporarily for debugging
# --------------------------------------------------
@app.route('/test')
def test_route():
    return "App is working! Blueprints loaded: " + ", ".join(loaded_blueprints)

# --------------------------------------------------
# RUN APP
# --------------------------------------------------

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))  # Changed default to 10000 for Render
    debug = os.getenv("FLASK_DEBUG", "False").lower() == "true"
    print(f"✅ Starting app on port {port} with debug={debug}")
    print(f"✅ Loaded blueprints: {loaded_blueprints}")
    app.run(host="0.0.0.0", port=port, debug=debug)
