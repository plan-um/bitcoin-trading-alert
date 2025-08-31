# 🚀 Bitcoin Trading Alert Dashboard

비트코인 투자 전략 대시보드 - Google/Kakao 로그인 지원

[![Deploy to Render](https://render.com/images/deploy-to-render-button.svg)](https://render.com/deploy?repo=https://github.com/plan-um/bitcoin-trading-alert)
[![Deploy on Railway](https://railway.app/button.svg)](https://railway.app/template/deploy?template=https://github.com/plan-um/bitcoin-trading-alert)

## 🔐 새로운 기능: OAuth 로그인
- **Google 로그인** 지원
- **Kakao 로그인** 지원
- 안전한 세션 관리
- 사용자별 대시보드 접근 제어

## 📊 주요 기능

- **반감기 사이클 분석** (30% 비중)
- **과열도 지표** (매도 신호)
  - Pi Cycle Top
  - NUPL (Net Unrealized Profit/Loss)
  - RSI (Relative Strength Index)
  - Google Trends
  - 김치 프리미엄
- **축적도 지표** (매수 신호)
  - Fear & Greed Index
  - Exchange Balance
  - Long-term Holder

## 🌟 현재 상태 (2025년 8월 기준)

- **반감기 사이클**: 4차 반감기(2024.4.20) 후 16개월
- **현재 국면**: 강세장 정점
- **권고사항**: 단계적 매도 시작 (월 10-20%)

## 🔧 환경 변수

Render/Railway 대시보드에서 설정:

```bash
# Flask 설정
FLASK_ENV=production
FLASK_SECRET_KEY=your-secret-key-here

# Google OAuth
GOOGLE_CLIENT_ID=your-google-client-id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your-google-client-secret

# Kakao OAuth
KAKAO_CLIENT_ID=your-kakao-rest-api-key

# Redirect URL (Render의 경우)
REDIRECT_URI_BASE=https://bitcoin-trading-alert.onrender.com
```

## 📱 사용법

1. Railway 배포 후 제공된 URL로 접속
2. 실시간 비트코인 가격 및 지표 확인
3. 매매 신호에 따라 투자 결정

## 🛠 기술 스택

- Python 3.11
- Flask
- Pandas, NumPy
- Chart.js
- shadcn/ui design

## 📄 라이선스

MIT License

## 🤝 기여

Issues와 Pull Requests 환영합니다!

---

Made with ❤️ for Bitcoin investors