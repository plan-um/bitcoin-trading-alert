# 비트코인 투자 전략 알람 시스템

매매 시점을 자동으로 알려주는 비트코인 투자 전략 시스템입니다.

## 주요 기능

### 🔥 과열도 모니터링 (매도 시점)
- Pi Cycle Top (30%)
- NUPL > 0.75 (25%)
- RSI 주간 > 85 (20%)
- 구글 트렌드 급증 (15%)
- 김치 프리미엄 > 10% (10%)

**단계별 청산 전략:**
- 30-50%: 20% 청산
- 50-70%: 누적 50% 청산
- 70-85%: 누적 80% 청산
- 85-100%: 완전 청산

### 💎 축적도 모니터링 (매수 시점)
- Fear & Greed Index < 30
- 거래소 BTC 잔고 감소 추세
- 장기 보유자 축적 증가
- 반감기 6-18개월 전 보너스

**DCA 전략:**
```
주간 투자금 = 기본금액 × (1 + (30 - 공포지수) / 100)
```

## 설치 방법

### 1. 필요 패키지 설치
```bash
pip install -r requirements.txt
```

### 2. macOS 알림 권한 설정
시스템 설정 > 알림 > Python 허용

## 실행 방법

### 통합 시스템 (추천)
과열도와 축적도를 모두 모니터링:
```bash
python bitcoin_complete_system.py
```

### 무료 API 버전
완전 무료 API만 사용:
```bash
python bitcoin_alert_free.py
```

### 기본 과열도만 모니터링
```bash
python bitcoin_alert_system.py
```

## 체크 간격 설정
환경변수로 체크 간격 조정 (기본 30분):
```bash
CHECK_INTERVAL=60 python bitcoin_complete_system.py
```

## 무료 API 정보

### ✅ 완전 무료
- **비트코인 가격**: CoinGecko, Binance API
- **한국 가격**: Bithumb, Upbit API
- **RSI, Pi Cycle**: 가격 데이터로 직접 계산
- **Fear & Greed**: Alternative.me API
- **구글 트렌드**: pytrends (제한 있음)
- **환율**: Dunamu API

### ⚠️ 제한사항
- **NUPL**: 정확한 온체인 데이터는 유료 (Glassnode $39/월)
  - 현재는 가격 기반 추정값 사용
- **거래소 잔고**: 실제 데이터는 유료
  - 변동성 기반 추정값 사용
- **장기 보유자**: 온체인 데이터 필요
  - 가격 패턴 기반 추정

## 로그 파일
- `bitcoin_strategy.log`: 실행 로그
- `bitcoin_strategy_status.json`: 현재 상태

## 주의사항
1. 투자 판단은 본인 책임
2. 지표는 참고용이며 100% 정확하지 않음
3. 무료 API는 호출 제한 있음
4. NUPL 등 일부 지표는 추정값 사용

## 업데이트 예정
- [ ] 텔레그램 봇 연동
- [ ] 웹 대시보드
- [ ] 백테스팅 기능
- [ ] 더 많은 온체인 지표