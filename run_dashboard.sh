#!/bin/bash

echo "🚀 비트코인 투자 전략 대시보드 시작..."
echo "=================================="

# 패키지 확인
echo "📦 필요 패키지 확인 중..."
pip install -r requirements.txt > /dev/null 2>&1

# 대시보드 실행
echo "🌐 웹 서버 시작..."
echo "=================================="
echo "✅ 대시보드 URL: http://localhost:5000"
echo "✅ 종료: Ctrl+C"
echo "=================================="

python dashboard.py