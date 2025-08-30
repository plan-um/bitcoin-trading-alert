from flask import Flask, render_template, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

@app.route('/')
def index():
    return render_template('dashboard_final.html')

@app.route('/health')
def health():
    return jsonify({"status": "healthy"})

@app.route('/api/data')
def get_data():
    return jsonify({"status": "initializing"})

@app.route('/api/history')
def get_history():
    return jsonify([])

@app.route('/api/status')
def get_status():
    return jsonify({"status": "ok"})

@app.route('/api/refresh')
def refresh_data():
    return jsonify({"status": "refreshing"})

if __name__ == '__main__':
    # 8080 포트 고정
    app.run(host='0.0.0.0', port=8080)