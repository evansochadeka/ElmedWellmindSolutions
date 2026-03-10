# create_superadmin.py
from app import app
from models import db, User
import secrets

def create_superadmin():
    """Create superadmin user"""
    with app.app_context():
        # Check if superadmin already exists
        superadmin = User.query.filter_by(email='elijahokware@gmail.com').first()
        
        if superadmin:
            print("✅ Superadmin already exists")
            return
        
        # Create superadmin
        admin = User(
            username='elijahokware',
            email='elijahokware@gmail.com',
            first_name='Elijah',
            last_name='Okware',
            role='superadmin',
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
        admin.set_password('Pa$$w0rd')
        
        db.session.add(admin)
        db.session.commit()
        
        print("✅ Superadmin created successfully!")
        print("   Email: elijahokware@gmail.com")
        print("   Password: Pa$$w0rd")

if __name__ == '__main__':
    create_superadmin()