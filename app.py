import os
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