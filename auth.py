"""
OAuth 2.0 Authentication Module
Supports Google and Kakao login
"""

import os
import json
from functools import wraps
from flask import redirect, url_for, session, request, jsonify
from flask_login import LoginManager, UserMixin, login_user, logout_user, current_user
from authlib.integrations.flask_client import OAuth
from datetime import datetime, timedelta
import secrets

class User(UserMixin):
    """Simple User class for Flask-Login"""
    def __init__(self, user_id, email, name, provider, picture=None):
        self.id = user_id
        self.email = email
        self.name = name
        self.provider = provider
        self.picture = picture
        self.created_at = datetime.now()

class AuthManager:
    def __init__(self, app=None):
        self.app = app
        self.oauth = None
        self.login_manager = None
        self.users = {}  # Simple in-memory user storage (use database in production)
        
        if app:
            self.init_app(app)
    
    def init_app(self, app):
        """Initialize authentication with Flask app"""
        self.app = app
        
        # Setup Flask-Login
        self.login_manager = LoginManager()
        self.login_manager.init_app(app)
        self.login_manager.login_view = 'login'
        
        # Setup OAuth
        self.oauth = OAuth(app)
        
        # Configure Google OAuth
        self.google = self.oauth.register(
            name='google',
            client_id=os.getenv('GOOGLE_CLIENT_ID'),
            client_secret=os.getenv('GOOGLE_CLIENT_SECRET'),
            server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
            client_kwargs={
                'scope': 'openid email profile'
            }
        )
        
        # Configure Kakao OAuth
        self.kakao = self.oauth.register(
            name='kakao',
            client_id=os.getenv('KAKAO_CLIENT_ID'),
            client_secret=os.getenv('KAKAO_CLIENT_SECRET'),
            access_token_url='https://kauth.kakao.com/oauth/token',
            access_token_params=None,
            authorize_url='https://kauth.kakao.com/oauth/authorize',
            authorize_params=None,
            api_base_url='https://kapi.kakao.com/',
            client_kwargs={'scope': 'profile_nickname profile_image account_email'},
        )
        
        @self.login_manager.user_loader
        def load_user(user_id):
            return self.users.get(user_id)
    
    def login_required(self, f):
        """Decorator to require login for routes"""
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                if request.is_json:
                    return jsonify({'error': 'Authentication required'}), 401
                return redirect(url_for('login', next=request.url))
            return f(*args, **kwargs)
        return decorated_function
    
    def google_login(self):
        """Initiate Google OAuth login"""
        redirect_uri = url_for('google_callback', _external=True)
        return self.google.authorize_redirect(redirect_uri)
    
    def google_callback(self):
        """Handle Google OAuth callback"""
        try:
            token = self.google.authorize_access_token()
            
            # Get user info from Google
            user_info = token.get('userinfo')
            if not user_info:
                # Fetch user info if not in token
                resp = self.google.get('https://www.googleapis.com/oauth2/v1/userinfo')
                user_info = resp.json()
            
            # Create or update user
            user_id = f"google_{user_info['id']}"
            user = User(
                user_id=user_id,
                email=user_info.get('email'),
                name=user_info.get('name'),
                provider='google',
                picture=user_info.get('picture')
            )
            
            # Store user in memory (use database in production)
            self.users[user_id] = user
            
            # Log in user
            login_user(user)
            
            # Redirect to dashboard or next page
            next_page = request.args.get('next')
            return redirect(next_page or url_for('index'))
            
        except Exception as e:
            print(f"Google login error: {e}")
            return redirect(url_for('login', error='google_auth_failed'))
    
    def kakao_login(self):
        """Initiate Kakao OAuth login"""
        redirect_uri = url_for('kakao_callback', _external=True)
        return self.kakao.authorize_redirect(redirect_uri)
    
    def kakao_callback(self):
        """Handle Kakao OAuth callback"""
        try:
            token = self.kakao.authorize_access_token()
            
            # Get user info from Kakao
            resp = self.kakao.get('v2/user/me', token=token)
            user_info = resp.json()
            
            # Extract user data
            kakao_account = user_info.get('kakao_account', {})
            profile = kakao_account.get('profile', {})
            
            # Create or update user
            user_id = f"kakao_{user_info['id']}"
            user = User(
                user_id=user_id,
                email=kakao_account.get('email'),
                name=profile.get('nickname'),
                provider='kakao',
                picture=profile.get('profile_image_url')
            )
            
            # Store user in memory (use database in production)
            self.users[user_id] = user
            
            # Log in user
            login_user(user)
            
            # Redirect to dashboard or next page
            next_page = request.args.get('next')
            return redirect(next_page or url_for('index'))
            
        except Exception as e:
            print(f"Kakao login error: {e}")
            return redirect(url_for('login', error='kakao_auth_failed'))
    
    def logout(self):
        """Log out current user"""
        logout_user()
        return redirect(url_for('login'))
    
    def get_current_user_info(self):
        """Get current user information"""
        if current_user.is_authenticated:
            return {
                'id': current_user.id,
                'email': current_user.email,
                'name': current_user.name,
                'provider': current_user.provider,
                'picture': current_user.picture
            }
        return None

def generate_secret_key():
    """Generate a secure secret key"""
    return secrets.token_hex(32)