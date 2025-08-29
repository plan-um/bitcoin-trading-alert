#!/usr/bin/env python3
"""
Railway 배포용 메인 앱
"""
import os
from dashboard_with_status import app, update_thread, update_single_data
import logging

# Railway 환경 설정
if os.getenv('RAILWAY_ENVIRONMENT'):
    app.config['ENV'] = 'production'
    app.config['DEBUG'] = False
    logging.basicConfig(level=logging.INFO)
else:
    app.config['ENV'] = 'development'
    app.config['DEBUG'] = True
    logging.basicConfig(level=logging.DEBUG)

# 초기 데이터 수집
print("🚀 Bitcoin Strategy Dashboard Starting...")
print("📊 Collecting initial data...")
update_single_data()
print("✅ Initial data collection complete")

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port, debug=False)