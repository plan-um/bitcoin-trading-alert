#!/usr/bin/env python3
"""
Railway 배포용 서버 - PORT 문제 완전 해결
"""
from flask import Flask, render_template, jsonify
import os
import sys

# Flask 앱 생성
app = Flask(__name__)

@app.route('/')
def index():
    return render_template('dashboard_final.html')

@app.route('/health')
def health():
    return jsonify({"status": "healthy"})

@app.route('/api/data')
def get_data():
    return jsonify({"status": "initializing", "message": "Loading data..."})

@app.route('/api/history')
def get_history():
    return jsonify([])

@app.route('/api/status')
def get_status():
    return jsonify({"status": "ok"})

@app.route('/api/refresh')
def refresh():
    return jsonify({"status": "refreshing"})

if __name__ == '__main__':
    # PORT 환경변수 디버깅
    raw_port = os.environ.get('PORT', '8080')
    print(f"DEBUG: Raw PORT from environment: '{raw_port}'")
    print(f"DEBUG: PORT type: {type(raw_port)}")
    print(f"DEBUG: All env vars: {dict(os.environ)}")
    
    # PORT 파싱 시도
    port = 8080  # 기본값
    
    # '$PORT' 문자열 체크
    if raw_port == '$PORT':
        print("WARNING: PORT is literal string '$PORT', using default 8080")
        port = 8080
    elif raw_port:
        try:
            # 숫자만 추출
            import re
            numbers = re.findall(r'\d+', raw_port)
            if numbers:
                port = int(numbers[0])
                print(f"Extracted port number: {port}")
            else:
                print(f"No numbers found in PORT: '{raw_port}', using 8080")
                port = 8080
        except Exception as e:
            print(f"Error parsing PORT: {e}, using 8080")
            port = 8080
    
    print(f"FINAL: Starting server on port {port}")
    
    # 서버 시작
    app.run(host='0.0.0.0', port=port, debug=False)