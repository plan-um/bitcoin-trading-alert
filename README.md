# 🚀 Bitcoin Trading Alert Dashboard

비트코인 투자 전략 대시보드 - 반감기 사이클 지표 포함

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

## 🚂 Deploy to Railway

[![Deploy on Railway](https://railway.app/button.svg)](https://railway.app/template/deploy?template=https://github.com/plan-um/bitcoin-trading-alert)

## 🔧 환경 변수

Railway 대시보드에서 설정:

```bash
FLASK_ENV=production
SECRET_KEY=your-secret-key-here
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