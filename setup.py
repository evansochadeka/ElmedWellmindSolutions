# setup.py
import os
import sys

def check_dependencies():
    print("🔍 Checking dependencies...")
    
    required = [
        'flask',
        'flask-cors',
        'flask-sqlalchemy',
        'python-dotenv',
        'requests'
    ]
    
    missing = []
    for package in required:
        try:
            __import__(package.replace('-', '_'))
            print(f"✅ {package}")
        except ImportError:
            missing.append(package)
            print(f"❌ {package}")
    
    if missing:
        print(f"\n⚠️  Missing packages: {', '.join(missing)}")
        print("📦 Installing missing packages...")
        os.system(f"{sys.executable} -m pip install {' '.join(missing)}")
    else:
        print("\n✅ All dependencies are installed!")
    
    return len(missing) == 0

def create_env_file():
    env_path = '.env'
    if not os.path.exists(env_path):
        print(f"\n📝 Creating {env_path} file...")
        with open(env_path, 'w') as f:
            f.write("""# Environment Variables for Kenyan Mental Health AI
COHERE_API_KEY=your_cohere_api_key_here
FLASK_SECRET_KEY=dev-secret-key-change-in-production
FLASK_DEBUG=True
DATABASE_URL=sqlite:///kenyan_health_ai.db
""")
        print(f"✅ Created {env_path}")
    else:
        print(f"\n✅ {env_path} already exists")

def create_folders():
    folders = ['static/images', 'templates']
    for folder in folders:
        if not os.path.exists(folder):
            os.makedirs(folder)
            print(f"✅ Created folder: {folder}")
        else:
            print(f"✅ Folder exists: {folder}")

if __name__ == "__main__":
    print("\n" + "="*60)
    print("🧠 Kenyan Mental Health AI - Setup Script")
    print("="*60)
    
    create_folders()
    create_env_file()
    if check_dependencies():
        print("\n✅ Setup completed successfully!")
        print("\n📋 Next steps:")
        print("1. Edit the .env file and add your Cohere API key")
        print("2. Add Kenya flag image to static/images/kenya-flag.gif")
        print("3. Run: python app.py")
        print("\n🌐 The application will be available at: http://localhost:5001")
    else:
        print("\n⚠️  Setup completed with warnings")