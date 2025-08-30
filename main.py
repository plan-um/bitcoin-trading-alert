#!/usr/bin/env python3
"""
Railway 최종 해결 - 고정 포트 8080
"""
from flask import Flask, render_template, jsonify

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('dashboard_final.html')

@app.route('/health')
def health():
    return jsonify({"status": "ok"})

@app.route('/api/data')
def data():
    return jsonify({"status": "loading"})

@app.route('/api/history')
def history():
    return jsonify([])

@app.route('/api/status')
def status():
    return jsonify({"status": "ok"})

@app.route('/api/refresh')
def refresh():
    return jsonify({"status": "ok"})

# 무조건 8080 포트 사용
if __name__ == '__main__':
    print("Starting on port 8080")
    app.run(host='0.0.0.0', port=8080, debug=False)