#!/usr/bin/env python3
"""
Railway 배포용 간단한 앱 - 헬스체크 문제 해결
"""
from flask import Flask, render_template, jsonify
from flask_cors import CORS
import os
import json
from datetime import datetime
from werkzeug.serving import run_simple

app = Flask(__name__)
CORS(app)

# 전역 데이터 (초기값)
latest_data = {
    "status": "initializing",
    "message": "Dashboard is starting up...",
    "timestamp": datetime.now().isoformat()
}

@app.route('/')
def index():
    """메인 대시보드 페이지"""
    return render_template('dashboard_final.html')

@app.route('/health')
def health():
    """헬스체크 엔드포인트"""
    return jsonify({"status": "healthy", "timestamp": datetime.now().isoformat()})

@app.route('/api/data')
def get_data():
    """현재 데이터 API"""
    return jsonify(latest_data)

@app.route('/api/history')
def get_history():
    """히스토리 데이터 API"""
    return jsonify([])

@app.route('/api/status')
def get_status():
    """데이터 소스 상태 API"""
    return jsonify({"status": "running"})

@app.route('/api/refresh')
def refresh_data():
    """강제 새로고침"""
    return jsonify({'status': 'refreshing'})

# 백그라운드에서 실제 데이터 로드
def load_real_data():
    try:
        from dashboard_with_status import system, update_single_data
        print("Loading real data system...")
        update_single_data()
        global latest_data
        if os.path.exists('dashboard_data.json'):
            with open('dashboard_data.json', 'r') as f:
                latest_data = json.load(f)
        print("Real data loaded successfully")
    except Exception as e:
        print(f"Error loading real data: {e}")
        latest_data["error"] = str(e)

# 앱 시작 시 백그라운드로 데이터 로드
import threading
threading.Thread(target=load_real_data, daemon=True).start()

if __name__ == '__main__':
    # Railway PORT 처리
    port_str = os.environ.get("PORT", "5000")
    try:
        port = int(port_str)
    except (ValueError, TypeError):
        print(f"Invalid PORT value: {port_str}, using default 5000")
        port = 5000
    
    print(f"Starting Flask app on port {port}")
    print(f"Environment PORT: {os.environ.get('PORT', 'not set')}")
    
    # 직접 Flask 서버 실행 (production에서는 gunicorn 사용)
    app.run(host='0.0.0.0', port=port, debug=False, threaded=True)