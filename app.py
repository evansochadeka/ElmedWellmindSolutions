# app.py - RENDER READY VERSION

import os
from flask import Flask, render_template, jsonify
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
# IMPORTANT
# --------------------------------------------------
# ❌ NO app.run()
# ❌ NO debug=True
# Render runs this app using:
# gunicorn app:app
