# app.py - UPDATED
import os
import sys
from flask import Flask, render_template, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
from extensions import db
from routes_py import api

# Load environment variables
load_dotenv()

app = Flask(__name__, 
            static_folder='static',
            template_folder='templates')
CORS(app)

# Database configuration
database_url = os.getenv("DATABASE_URL", "sqlite:///elmed_wellmind.db")
app.config["SQLALCHEMY_DATABASE_URI"] = database_url
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SECRET_KEY"] = os.getenv("FLASK_SECRET_KEY", "dev-secret-key-change-me-in-production")

# Initialize extensions
db.init_app(app)

# Register API blueprint
app.register_blueprint(api)

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/chat')
def chat_interface():
    return render_template('chat.html')

@app.route('/health')
def health_check():
    ai_status = "active" if os.getenv("COHERE_API_KEY") else "inactive"
    return jsonify({
        "status": "healthy", 
        "service": "Elmed Wellmind Mental Health AI",
        "ai_status": ai_status,
        "database": "connected",
        "api_base": "https://api.cohere.com/v1"
    })

def initialize_database():
    with app.app_context():
        try:
            # Drop all tables and recreate
            db.drop_all()
            db.create_all()
            print("✅ Database initialized successfully!")
        except Exception as e:
            print(f"⚠️ Database initialization warning: {e}")

def test_cohere_models():
    """Test which Cohere models are available"""
    cohere_key = os.getenv("COHERE_API_KEY")
    if not cohere_key:
        return None
    
    try:
        import requests
        
        # First, get available models
        models_response = requests.get(
            'https://api.cohere.com/v1/models',
            headers={'Authorization': f'Bearer {cohere_key}'},
            timeout=10
        )
        
        if models_response.status_code != 200:
            return None
        
        models = models_response.json().get('models', [])
        
        # Try to find chat models
        chat_models_to_try = [
            'command-r-08-2024',
            'command-r-plus-08-2024',
            'command-r',
            'command-r-plus',
            'aya-23-8B',
            'aya-23-35B'
        ]
        
        working_models = []
        for model in chat_models_to_try:
            if model in models:
                # Quick test
                try:
                    test_response = requests.post(
                        'https://api.cohere.com/v1/chat',
                        headers={
                            'Authorization': f'Bearer {cohere_key}',
                            'Content-Type': 'application/json'
                        },
                        json={
                            'model': model,
                            'message': 'test',
                            'max_tokens': 10
                        },
                        timeout=5
                    )
                    
                    if test_response.status_code == 200:
                        working_models.append(model)
                except:
                    continue
        
        return working_models
        
    except Exception as e:
        print(f"❌ Error testing Cohere models: {e}")
        return None

if __name__ == "__main__":
    # Initialize database
    initialize_database()
    
    print("\n" + "="*70)
    print("🧠 ELMED WELLMIND - KENYAN MENTAL HEALTH AI PLATFORM")
    print("="*70)
    print("🌐 Main Website: http://localhost:5001/")
    print("💬 AI Chat Interface: http://localhost:5001/chat")
    print("🩺 Health Check: http://localhost:5001/health")
    
    # Check Cohere API
    cohere_key = os.getenv("COHERE_API_KEY")
    if cohere_key:
        print(f"\n🔍 Checking Cohere API...")
        
        # Test available models
        working_models = test_cohere_models()
        
        if working_models:
            print(f"✅ AI Status: ACTIVE")
            print(f"   Available models: {', '.join(working_models[:3])}")
            print(f"   Using primary model: {working_models[0]}")
        else:
            print("⚠️ AI Status: LIMITED FUNCTIONALITY")
            print("   No working chat models found with your API key")
            print("   The AI will use intelligent fallback responses")
            print("   Check your Cohere dashboard for available models")
    else:
        print("❌ AI Status: FALLBACK MODE (No API key)")
        print("   Add COHERE_API_KEY to your .env file for AI responses")
        print("   Currently using intelligent fallback responses")
    
    print("\n🧠 AI Features:")
    print("   - Intelligent fallback responses for all queries")
    print("   - Context-aware emergency detection")
    print("   - Culturally appropriate Kenyan mental health support")
    print("   - 24/7 emergency contact: +254759226354")
    
    print("\n📡 API Endpoints:")
    print("   - POST /api/chat                  - AI Mental Health Assistant")
    print("   - GET  /api/chat/history/<session>- Chat history")
    print("   - GET  /api/community/posts       - Community posts")
    print("   - POST /api/community/posts       - Create post")
    print("   - POST /api/community/posts/<id>/like - Like post")
    print("   - GET  /api/emergency             - Emergency contacts")
    print("   - GET  /api/categories            - Health categories")
    print("="*70 + "\n")
    
    app.run(host="0.0.0.0", port=5001, debug=True)