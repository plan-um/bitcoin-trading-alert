#!/bin/bash

echo "🚂 Railway 배포 스크립트"
echo "========================"

# Git 상태 확인
if [ ! -d .git ]; then
    echo "📦 Git 초기화..."
    git init
fi

# 파일 추가 및 커밋
echo "📝 파일 준비..."
git add .
git commit -m "Deploy to Railway: $(date +%Y-%m-%d_%H:%M:%S)"

# GitHub 원격 저장소 확인
if ! git remote | grep -q origin; then
    echo "⚠️  GitHub 저장소를 먼저 생성하고 연결해주세요:"
    echo "1. https://github.com/new 에서 'bitcoin-trading-alert' 저장소 생성"
    echo "2. 다음 명령어 실행:"
    echo "   git remote add origin https://github.com/YOUR_USERNAME/bitcoin-trading-alert.git"
    echo "3. 다시 이 스크립트 실행"
    exit 1
fi

# Push to GitHub
echo "🚀 GitHub에 푸시..."
git push -u origin main

echo "✅ GitHub 푸시 완료!"
echo ""
echo "📌 다음 단계:"
echo "1. https://railway.app 접속"
echo "2. 'New Project' → 'Deploy from GitHub repo' 선택"
echo "3. 'bitcoin-trading-alert' 저장소 선택"
echo "4. 배포 완료 대기 (약 2-3분)"
echo ""
echo "🔧 환경변수 설정 (Railway 대시보드에서):"
echo "   FLASK_ENV=production"
echo "   SECRET_KEY=$(openssl rand -hex 32)"
echo ""
echo "🎉 완료!"