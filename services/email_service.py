# services/email_service.py
"""Email service for sending notifications"""
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from flask import current_app
import os

class EmailService:
    """Handle email sending"""
    
    @staticmethod
    def send_email(to_email, subject, html_content, text_content=None):
        """Send an email"""
        try:
            # Get email configuration from environment
            smtp_server = os.environ.get('SMTP_SERVER', 'smtp.gmail.com')
            smtp_port = int(os.environ.get('SMTP_PORT', 587))
            smtp_username = os.environ.get('SMTP_USERNAME')
            smtp_password = os.environ.get('SMTP_PASSWORD')
            from_email = os.environ.get('FROM_EMAIL', 'noreply@elmedwellmind.com')
            
            if not smtp_username or not smtp_password:
                print(f"📧 Email would be sent to {to_email}: {subject}")
                return True
            
            # Create message
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = from_email
            msg['To'] = to_email
            
            # Add plain text version
            if text_content:
                msg.attach(MIMEText(text_content, 'plain'))
            
            # Add HTML version
            msg.attach(MIMEText(html_content, 'html'))
            
            # Send email
            with smtplib.SMTP(smtp_server, smtp_port) as server:
                server.starttls()
                server.login(smtp_username, smtp_password)
                server.send_message(msg)
            
            print(f"✅ Email sent to {to_email}")
            return True
            
        except Exception as e:
            current_app.logger.error(f"Email error: {str(e)}")
            return False
    
    @staticmethod
    def send_welcome_email(user):
        """Send welcome email to new user"""
        subject = "Welcome to Elmed Wellmind Solutions!"
        html_content = f"""
        <html>
            <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                    <h1 style="color: #6C63FF;">Welcome to Elmed Wellmind Solutions!</h1>
                    <p>Hi {user.first_name},</p>
                    <p>Thank you for joining our community. We're here to support you on your mental wellness journey.</p>
                    
                    <div style="background: #f8f9ff; padding: 20px; border-radius: 10px; margin: 20px 0;">
                        <h3 style="color: #6C63FF; margin-top: 0;">Next Steps:</h3>
                        <ul>
                            <li>Complete your profile</li>
                            <li>Browse available professionals</li>
                            <li>Book your first session</li>
                        </ul>
                    </div>
                    
                    <p>If you have any questions, we're here to help.</p>
                    
                    <div style="margin-top: 30px; padding-top: 20px; border-top: 1px solid #eee;">
                        <p style="color: #999; font-size: 12px;">
                            Elmed Wellmind Solutions<br>
                            Kahawa Wendani, Thika Road<br>
                            Nairobi, Kenya<br>
                            <a href="tel:+254759226354">+254 759 226354</a>
                        </p>
                    </div>
                </div>
            </body>
        </html>
        """
        
        return EmailService.send_email(user.email, subject, html_content)
    
    @staticmethod
    def send_password_reset(user, reset_link):
        """Send password reset email"""
        subject = "Password Reset Request"
        html_content = f"""
        <html>
            <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                    <h1 style="color: #6C63FF;">Password Reset Request</h1>
                    <p>Hi {user.first_name},</p>
                    <p>We received a request to reset your password. Click the button below to reset it:</p>
                    
                    <div style="text-align: center; margin: 30px 0;">
                        <a href="{reset_link}" style="background: linear-gradient(135deg, #6C63FF, #36D1DC); color: white; padding: 15px 30px; text-decoration: none; border-radius: 50px; display: inline-block;">Reset Password</a>
                    </div>
                    
                    <p>If you didn't request this, you can safely ignore this email.</p>
                    <p>This link will expire in 24 hours.</p>
                    
                    <div style="margin-top: 30px; padding-top: 20px; border-top: 1px solid #eee;">
                        <p style="color: #999; font-size: 12px;">
                            Elmed Wellmind Solutions<br>
                            Kahawa Wendani, Thika Road<br>
                            Nairobi, Kenya
                        </p>
                    </div>
                </div>
            </body>
        </html>
        """
        
        return EmailService.send_email(user.email, subject, html_content)