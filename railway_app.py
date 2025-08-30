#!/usr/bin/env python3
"""
Railway 전용 앱 - PORT 문제 해결
"""
from flask import Flask, render_template, jsonify
import os
import sys

# PORT 확인 및 설정
port = 5000  # 기본값
if 'PORT' in os.environ:
    try:
        port = int(os.environ['PORT'])
        print(f"Using PORT from environment: {port}")
    except:
        print(f"Invalid PORT in environment: {os.environ['PORT']}, using 5000")
        port = 5000
else:
    print("No PORT in environment, using 5000")

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('dashboard_final.html')

@app.route('/health')
def health():
    return jsonify({"status": "healthy", "port": port})

@app.route('/api/data')
def get_data():
    return jsonify({
        "status": "running",
        "message": "Dashboard is loading data...",
        "port": port
    })

@app.route('/api/history')
def get_history():
    return jsonify([])

@app.route('/api/status')
def get_status():
    return jsonify({"status": "running"})

@app.route('/api/refresh')
def refresh_data():
    return jsonify({'status': 'refreshing'})

if __name__ == '__main__':
    print(f"Starting Railway app on port {port}")
    print(f"Python version: {sys.version}")
    print(f"Environment variables: {list(os.environ.keys())}")
    
    # Waitress 서버 사용 (더 안정적)
    try:
        from waitress import serve
        print(f"Starting with Waitress on port {port}")
        serve(app, host='0.0.0.0', port=port)
    except ImportError:
        print(f"Waitress not available, using Flask development server on port {port}")
        app.run(host='0.0.0.0', port=port, debug=False)