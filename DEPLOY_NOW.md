# 🚀 즉시 배포하기

## 방법 1: Deploy to Render 버튼 (권장)

### 1단계: 아래 링크 클릭
[**🚀 Render에 배포하기**](https://render.com/deploy?repo=https://github.com/plan-um/bitcoin-trading-alert)

또는 URL 직접 복사:
```
https://render.com/deploy?repo=https://github.com/plan-um/bitcoin-trading-alert
```

### 2단계: Render 계정 연결
1. "Connect GitHub account" 클릭
2. GitHub 로그인 및 권한 부여
3. `plan-um/bitcoin-trading-alert` 저장소 선택

### 3단계: 서비스 생성
1. Service Name: `bitcoin-trading-alert` (또는 원하는 이름)
2. Region: `Singapore` 선택 (아시아 지역)
3. Branch: `main`
4. "Create Web Service" 클릭

### 4단계: 환경 변수 설정
배포가 시작된 후 Render Dashboard에서:

1. **Environment** 탭 클릭
2. **Add Environment Variable** 클릭
3. 다음 변수들 추가:

```
FLASK_SECRET_KEY = (자동 생성됨)
GOOGLE_CLIENT_ID = your-google-client-id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET = your-google-client-secret
KAKAO_CLIENT_ID = your-kakao-rest-api-key
REDIRECT_URI_BASE = https://bitcoin-trading-alert.onrender.com
```

---

## 방법 2: Render Dashboard에서 수동 생성

### 1. [Render Dashboard](https://dashboard.render.com) 접속

### 2. New + → Web Service

### 3. 저장소 연결
- Public Git repository 선택
- Repository URL: `https://github.com/plan-um/bitcoin-trading-alert`

### 4. 서비스 설정
```
Name: bitcoin-trading-alert
Region: Singapore
Branch: main
Runtime: Python 3
Build Command: pip install -r requirements.txt
Start Command: gunicorn app_with_auth:app
```

### 5. 환경 변수 추가 (위와 동일)

---

## 📱 OAuth 앱 설정

### Google OAuth
1. [Google Cloud Console](https://console.cloud.google.com) 접속
2. OAuth 2.0 클라이언트 생성
3. 승인된 리디렉션 URI 추가:
   - `https://bitcoin-trading-alert.onrender.com/auth/google/callback`

### Kakao OAuth
1. [Kakao Developers](https://developers.kakao.com) 접속
2. 앱 생성 및 플랫폼 등록
3. Redirect URI 추가:
   - `https://bitcoin-trading-alert.onrender.com/auth/kakao/callback`

---

## ✅ 배포 확인

### 배포 상태
- Render Dashboard → Logs 탭에서 실시간 확인
- 빌드 완료까지 약 2-5분 소요

### 접속 URL
```
로그인: https://bitcoin-trading-alert.onrender.com/login
대시보드: https://bitcoin-trading-alert.onrender.com/
Health: https://bitcoin-trading-alert.onrender.com/health
```

### 테스트
1. Health Check: `/health` 엔드포인트 접속
2. 로그인 페이지 확인
3. OAuth 로그인 테스트

---

## 🆘 문제 해결

### "Build failed"
- requirements.txt 확인
- Python 버전 호환성 확인

### "OAuth 로그인 실패"
- 환경 변수 확인
- 리다이렉트 URI 정확히 일치하는지 확인
- OAuth 앱이 활성화되었는지 확인

### "Service unavailable"
- Free 플랜은 15분 후 슬립 모드
- 첫 요청 시 10-30초 대기

---

## 💡 팁

- **Custom Domain**: Settings → Custom Domains에서 설정
- **Auto Deploy**: GitHub 푸시 시 자동 재배포
- **Logs**: 실시간 로그로 디버깅
- **Metrics**: CPU, 메모리 사용량 모니터링

---

## 📞 지원

- [Render 문서](https://render.com/docs)
- [Render 상태](https://status.render.com)
- [Community Forum](https://community.render.com)