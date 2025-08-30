import os
import json
import threading
from flask import Flask, render_template, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

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

@app.route('/')
def index():
    return render_template('dashboard_final.html')

@app.route('/health')
def health():
    return jsonify({"status": "healthy"})

@app.route('/api/data')
def get_data():
    if latest_data:
        return jsonify(latest_data)
    return jsonify({"status": "loading", "message": "Data is being loaded..."})

@app.route('/api/history')
def get_history():
    return jsonify(historical_data)

@app.route('/api/status')
def get_status():
    return jsonify({"status": "ok"})

@app.route('/api/refresh')
def refresh_data():
    try:
        from dashboard_with_status import update_single_data
        threading.Thread(target=update_single_data, daemon=True).start()
        return jsonify({"status": "refreshing"})
    except:
        return jsonify({"status": "error"})

# 앱 시작 시 데이터 로드
threading.Thread(target=load_dashboard_data, daemon=True).start()

if __name__ == '__main__':
    # Railway의 PORT 처리
    port = None
    port_env = os.environ.get('PORT', '')
    
    # PORT가 '$PORT' 문자열이거나 비어있으면 8080 사용
    if port_env == '$PORT' or port_env == '${PORT}' or not port_env:
        port = 8080
    else:
        try:
            port = int(port_env)
        except:
            port = 8080
    
    print(f"Starting on port: {port}")
    app.run(host='0.0.0.0', port=port, debug=False)