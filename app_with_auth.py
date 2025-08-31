import os
import json
import threading
from datetime import timedelta
from flask import Flask, render_template, jsonify, redirect, url_for, session, request
from flask_cors import CORS
from flask_session import Session
from dotenv import load_dotenv
from auth import AuthManager, generate_secret_key

# Load environment variables
load_dotenv()

app = Flask(__name__)
CORS(app)

# Configure Flask app
app.config['SECRET_KEY'] = os.getenv('FLASK_SECRET_KEY', generate_secret_key())
app.config['SESSION_TYPE'] = 'filesystem'
app.config['SESSION_PERMANENT'] = False
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=7)
app.config['SESSION_COOKIE_SECURE'] = os.getenv('FLASK_ENV') == 'production'
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'

# Initialize session
Session(app)

# Initialize authentication
auth_manager = AuthManager(app)

# 전역 데이터
latest_data = {}
historical_data = []

def load_dashboard_data():
    """대시보드 데이터 로드"""
    global latest_data, historical_data
    try:
        # 실제 대시보드 시스템 임포트
        from dashboard_with_status import system, update_single_data
        print("Loading dashboard system...")
        
        # 초기 데이터 수집
        update_single_data()
        
        # JSON 파일에서 데이터 로드
        if os.path.exists('dashboard_data.json'):
            try:
                with open('dashboard_data.json', 'r') as f:
                    content = f.read()
                    if content.strip():  # 파일이 비어있지 않은 경우
                        latest_data = json.loads(content)
                        print("Dashboard data loaded successfully")
                    else:
                        print("Dashboard data file is empty")
            except (json.JSONDecodeError, Exception) as e:
                print(f"Error loading dashboard data: {e}")
                latest_data = {}
        
        # 백그라운드 업데이트 시작
        from dashboard_with_status import update_thread
        print("Background updates started")
        
    except Exception as e:
        print(f"Error loading dashboard: {e}")
        latest_data = {
            "error": str(e),
            "status": "Error loading data"
        }

# Routes
@app.route('/login')
def login():
    """Login page"""
    return render_template('login.html')

@app.route('/logout')
def logout():
    """Logout user"""
    return auth_manager.logout()

# OAuth routes
@app.route('/auth/google')
def google_login():
    """Google OAuth login"""
    return auth_manager.google_login()

@app.route('/auth/google/callback')
def google_callback():
    """Google OAuth callback"""
    return auth_manager.google_callback()

@app.route('/auth/kakao')
def kakao_login():
    """Kakao OAuth login"""
    return auth_manager.kakao_login()

@app.route('/auth/kakao/callback')
def kakao_callback():
    """Kakao OAuth callback"""
    return auth_manager.kakao_callback()

@app.route('/')
@auth_manager.login_required
def index():
    """Main dashboard (requires login)"""
    return render_template('dashboard_final.html')

@app.route('/health')
def health():
    """Health check endpoint"""
    return jsonify({"status": "healthy"})

@app.route('/api/user')
@auth_manager.login_required
def get_user():
    """Get current user info"""
    user_info = auth_manager.get_current_user_info()
    return jsonify(user_info)

@app.route('/api/data')
@auth_manager.login_required
def get_data():
    """Get dashboard data (requires login)"""
    if latest_data:
        return jsonify(latest_data)
    return jsonify({"status": "loading", "message": "Data is being loaded..."})

@app.route('/api/history')
@auth_manager.login_required
def get_history():
    """Get historical data (requires login)"""
    # Handle time range parameter
    time_range = request.args.get('range', 'day')
    
    # Filter historical data based on time range
    # This is a placeholder - implement actual filtering logic
    filtered_data = historical_data
    
    return jsonify(filtered_data)

@app.route('/api/status')
def get_status():
    """Get API status"""
    return jsonify({"status": "ok"})

@app.route('/api/refresh')
@auth_manager.login_required
def refresh_data():
    """Refresh dashboard data (requires login)"""
    try:
        from dashboard_with_status import update_single_data
        threading.Thread(target=update_single_data, daemon=True).start()
        return jsonify({"status": "refreshing"})
    except:
        return jsonify({"status": "error"})

# Load dashboard data on startup
threading.Thread(target=load_dashboard_data, daemon=True).start()

if __name__ == '__main__':
    # Render/Railway의 PORT 처리
    port = None
    port_env = os.environ.get('PORT', '')
    
    # PORT가 '$PORT' 문자열이거나 비어있으면 기본값 사용
    # Render는 보통 10000 포트 사용
    if port_env == '$PORT' or port_env == '${PORT}' or not port_env:
        port = 10000 if os.environ.get('RENDER') else 8080
    else:
        try:
            port = int(port_env)
        except:
            port = 10000 if os.environ.get('RENDER') else 8080
    
    # Print OAuth setup instructions
    print("\n" + "="*60)
    print("OAuth Setup Instructions:")
    print("="*60)
    print("\n1. Google OAuth Setup:")
    print("   - Go to: https://console.cloud.google.com/")
    print("   - Create a new project or select existing")
    print("   - Enable Google+ API")
    print("   - Create OAuth 2.0 credentials")
    print("   - Add authorized redirect URIs:")
    print(f"     * http://localhost:{port}/auth/google/callback")
    print("     * https://your-app.onrender.com/auth/google/callback")
    print("     * https://your-app.up.railway.app/auth/google/callback")
    print("\n2. Kakao OAuth Setup:")
    print("   - Go to: https://developers.kakao.com/")
    print("   - Create a new application")
    print("   - Get REST API key")
    print("   - Add redirect URIs in platform settings:")
    print(f"     * http://localhost:{port}/auth/kakao/callback")
    print("     * https://your-app.onrender.com/auth/kakao/callback")
    print("     * https://your-app.up.railway.app/auth/kakao/callback")
    print("\n3. Create .env file with your credentials")
    print("   Copy .env.example to .env and fill in your keys")
    print("="*60)
    print(f"\nStarting on port: {port}")
    print(f"Access the app at: http://localhost:{port}/login")
    print("="*60 + "\n")
    
    app.run(host='0.0.0.0', port=port, debug=False)