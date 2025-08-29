# 🚀 비트코인 투자 전략 대시보드 배포 가이드

## 📋 배포 옵션 비교

### 1. **Heroku (무료 → 유료)**
- ✅ 장점: 쉬운 배포, 자동 HTTPS, 관리 편의
- ❌ 단점: 무료 플랜 종료, 최소 $5/월
- 적합한 경우: 빠른 배포, 관리 최소화

### 2. **Railway (추천) 🌟**
- ✅ 장점: 무료 크레딧 $5/월, 간단한 배포
- ✅ GitHub 연동, 자동 배포
- ❌ 단점: 무료 크레딧 소진 후 유료
- 적합한 경우: 초기 테스트 및 소규모 운영

### 3. **Render (무료 가능)**
- ✅ 장점: 무료 플랜 제공, 자동 HTTPS
- ❌ 단점: 무료 플랜 느림, 15분 후 슬립
- 적합한 경우: 개인 프로젝트

### 4. **AWS EC2 (프리티어)**
- ✅ 장점: 1년 무료, 완전한 제어
- ❌ 단점: 설정 복잡, 관리 필요
- 적합한 경우: 전문적인 운영

### 5. **Vercel/Netlify (정적 호스팅)**
- ❌ Python 백엔드 미지원
- API만 분리 배포 시 가능

---

## 🎯 추천: Railway 배포 방법

### 사전 준비

1. **GitHub 리포지토리 생성**
```bash
git init
git add .
git commit -m "Initial commit"
git remote add origin https://github.com/YOUR_USERNAME/bitcoin-trading-alert.git
git push -u origin main
```

2. **환경 변수 파일 생성**
`.env` 파일:
```env
FLASK_ENV=production
CHECK_INTERVAL=30
```

3. **requirements.txt 확인**
```txt
flask>=3.0.0
flask-cors>=4.0.0
requests>=2.31.0
pandas>=2.0.0
numpy>=1.24.0
plyer>=2.1.0
pytrends>=4.9.0
schedule>=1.2.0
gunicorn>=21.2.0  # 프로덕션 서버 추가
```

4. **Procfile 생성** (Railway/Heroku용)
```
web: gunicorn dashboard_with_status:app --bind 0.0.0.0:$PORT
```

5. **runtime.txt 생성** (Python 버전 지정)
```
python-3.11.0
```

### Railway 배포 단계

1. **Railway 계정 생성**
   - https://railway.app 접속
   - GitHub로 로그인

2. **새 프로젝트 생성**
   - "New Project" 클릭
   - "Deploy from GitHub repo" 선택
   - 리포지토리 선택

3. **환경 변수 설정**
   - Settings → Variables
   - `PORT`: 자동 설정됨
   - `CHECK_INTERVAL`: 30

4. **배포 확인**
   - 자동으로 빌드 및 배포 시작
   - Deployments 탭에서 진행 상황 확인
   - 생성된 URL로 접속

---

## 🐳 Docker 배포 (고급)

### Dockerfile 생성
```dockerfile
FROM python:3.11-slim

WORKDIR /app

# 시스템 패키지 설치
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Python 패키지 설치
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 앱 코드 복사
COPY . .

# 포트 노출
EXPOSE 5000

# 앱 실행
CMD ["gunicorn", "dashboard_with_status:app", "--bind", "0.0.0.0:5000", "--workers", "2"]
```

### docker-compose.yml
```yaml
version: '3.8'

services:
  web:
    build: .
    ports:
      - "5000:5000"
    environment:
      - FLASK_ENV=production
      - CHECK_INTERVAL=30
    restart: unless-stopped
    volumes:
      - ./data:/app/data  # 데이터 지속성
```

### Docker 실행
```bash
# 빌드
docker-compose build

# 실행
docker-compose up -d

# 로그 확인
docker-compose logs -f
```

---

## ⚙️ 프로덕션 최적화

### 1. **보안 강화**

`config.py` 생성:
```python
import os
from datetime import timedelta

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-this'
    
    # API 제한
    RATELIMIT_STORAGE_URL = "redis://localhost:6379"
    
    # CORS 설정
    CORS_ORIGINS = os.environ.get('CORS_ORIGINS', '*').split(',')
    
    # 캐시 설정
    CACHE_TYPE = "simple"
    CACHE_DEFAULT_TIMEOUT = 300
```

### 2. **성능 최적화**

`dashboard_production.py`:
```python
from flask_caching import Cache
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

# 캐시 설정
cache = Cache(app, config={'CACHE_TYPE': 'simple'})

# API 제한
limiter = Limiter(
    app,
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"]
)

@app.route('/api/data')
@cache.cached(timeout=30)  # 30초 캐시
@limiter.limit("10 per minute")
def get_data():
    return jsonify(latest_data)
```

### 3. **모니터링 추가**

`requirements.txt`에 추가:
```txt
prometheus-flask-exporter>=0.21.0
sentry-sdk[flask]>=1.39.0
```

`app.py`에 추가:
```python
import sentry_sdk
from sentry_sdk.integrations.flask import FlaskIntegration

sentry_sdk.init(
    dsn=os.environ.get('SENTRY_DSN'),
    integrations=[FlaskIntegration()],
    traces_sample_rate=1.0
)
```

---

## 🌐 도메인 연결

### 1. **도메인 구매**
- Namecheap, GoDaddy, 가비아 등

### 2. **DNS 설정**
```
A Record: @ → Railway/Render IP
CNAME: www → 앱 URL
```

### 3. **HTTPS 설정**
- Railway/Render: 자동 설정
- 자체 서버: Let's Encrypt 사용

---

## 📊 프로덕션 체크리스트

### 배포 전 확인사항
- [ ] 모든 API 키 환경변수로 분리
- [ ] 에러 핸들링 추가
- [ ] 로깅 시스템 구축
- [ ] 테스트 코드 작성
- [ ] 보안 헤더 설정
- [ ] CORS 설정 확인
- [ ] 데이터베이스 백업 계획
- [ ] 모니터링 시스템 구축

### 보안 체크리스트
- [ ] SECRET_KEY 변경
- [ ] DEBUG = False 설정
- [ ] HTTPS 강제 적용
- [ ] SQL Injection 방지
- [ ] XSS 방지
- [ ] CSRF 토큰 설정
- [ ] Rate Limiting 적용

---

## 🔧 트러블슈팅

### 1. **포트 문제**
```python
# Heroku/Railway는 PORT 환경변수 사용
port = int(os.environ.get('PORT', 5000))
app.run(host='0.0.0.0', port=port)
```

### 2. **시간대 문제**
```python
# UTC → KST 변환
from pytz import timezone
KST = timezone('Asia/Seoul')
datetime.now(KST)
```

### 3. **메모리 문제**
- Worker 수 조정: `--workers 2`
- 캐시 적극 활용
- 불필요한 데이터 정리

### 4. **API 제한 문제**
- 캐싱 적용
- 요청 간격 조정
- 여러 API 소스 분산

---

## 📱 모바일 앱 배포 (선택사항)

### PWA (Progressive Web App) 변환

`manifest.json` 생성:
```json
{
  "name": "Bitcoin Strategy Dashboard",
  "short_name": "BTC Dashboard",
  "description": "Bitcoin trading strategy monitoring",
  "start_url": "/",
  "display": "standalone",
  "background_color": "#ffffff",
  "theme_color": "#667eea",
  "icons": [
    {
      "src": "/static/icon-192.png",
      "sizes": "192x192",
      "type": "image/png"
    },
    {
      "src": "/static/icon-512.png",
      "sizes": "512x512",
      "type": "image/png"
    }
  ]
}
```

HTML에 추가:
```html
<link rel="manifest" href="/manifest.json">
<meta name="apple-mobile-web-app-capable" content="yes">
```

---

## 💰 비용 예상

### 월별 운영 비용
1. **Railway**: $0~5 (무료 크레딧)
2. **Render**: $0 (무료 플랜) / $7 (기본)
3. **Heroku**: $5 (Eco)
4. **AWS EC2**: $0 (프리티어) / ~$10
5. **VPS**: $5~20 (Vultr, DigitalOcean)

### 추가 비용
- 도메인: ~$15/년
- SSL: 무료 (Let's Encrypt)
- 모니터링: 무료~$10/월

---

## 🎯 추천 배포 순서

### 초보자
1. Railway 무료 크레딧으로 시작
2. 트래픽 증가 시 유료 플랜 전환
3. 필요시 AWS/GCP로 이전

### 중급자
1. Docker 컨테이너화
2. AWS EC2 프리티어 활용
3. CI/CD 파이프라인 구축

### 전문가
1. Kubernetes 클러스터 구성
2. 마이크로서비스 아키텍처
3. 자동 스케일링 설정

---

## 📞 지원 및 문의

- GitHub Issues: 버그 리포트
- 이메일: your-email@example.com
- 디스코드: 커뮤니티 지원

---

## 📚 참고 자료

- [Railway 문서](https://docs.railway.app)
- [Flask 배포 가이드](https://flask.palletsprojects.com/deploying/)
- [Docker 베스트 프랙티스](https://docs.docker.com/develop/dev-best-practices/)
- [Python 프로덕션 가이드](https://realpython.com/python-web-applications/)