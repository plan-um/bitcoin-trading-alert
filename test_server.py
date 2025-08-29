from flask import Flask
import sys

app = Flask(__name__)

@app.route('/')
def hello():
    return "Flask is working!"

if __name__ == '__main__':
    print("Starting test server on http://localhost:5000", file=sys.stderr)
    app.run(debug=False, port=5000, host='0.0.0.0')