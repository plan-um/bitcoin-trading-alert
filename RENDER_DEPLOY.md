# Render 배포 가이드

## 사전 준비사항

1. [Render](https://render.com) 계정 생성
2. GitHub 저장소에 코드가 푸시되어 있어야 함
3. Google OAuth 및 Kakao OAuth 앱이 설정되어 있어야 함

## 배포 단계

### 1. GitHub 연결

1. Render 대시보드에서 "New +" → "Web Service" 클릭
2. GitHub 계정 연결
3. `bitcoin-trading-alert` 저장소 선택

### 2. 서비스 설정

#### 기본 설정
- **Name**: `bitcoin-trading-alert` (또는 원하는 이름)
- **Region**: Singapore (아시아) 또는 Oregon (미국)
- **Branch**: `main`
- **Runtime**: Python 3

#### 빌드 및 시작 명령
- **Build Command**: `./build.sh` 또는 `pip install -r requirements.txt`
- **Start Command**: `./start.sh` 또는 `gunicorn app_with_auth:app`

#### 인스턴스 타입
- **Free** 플랜으로 시작 (월 750시간 무료)
- 필요시 Starter ($7/월) 이상으로 업그레이드

### 3. 환경 변수 설정

Render 대시보드 → Environment → Add Environment Variable

필수 환경 변수:

```bash
# Flask 설정
FLASK_SECRET_KEY=<강력한 랜덤 키 생성>
FLASK_ENV=production

# Google OAuth 2.0
GOOGLE_CLIENT_ID=<구글 클라이언트 ID>
GOOGLE_CLIENT_SECRET=<구글 시크릿>

# Kakao OAuth 2.0
KAKAO_CLIENT_ID=<카카오 REST API 키>

# Render URL (자동 생성된 URL 사용)
REDIRECT_URI_BASE=https://<your-app-name>.onrender.com

# Python 버전 (선택사항)
PYTHON_VERSION=3.11.0
```

### 4. OAuth 리다이렉트 URI 업데이트

배포 후 생성된 Render URL을 OAuth 설정에 추가:

#### Google Cloud Console
1. API 및 서비스 → 사용자 인증 정보
2. OAuth 2.0 클라이언트 ID 수정
3. 승인된 리디렉션 URI 추가:
   - `https://<your-app-name>.onrender.com/auth/google/callback`

#### Kakao Developers
1. 내 애플리케이션 → 앱 설정
2. 플랫폼 → Web 플랫폼 도메인 추가:
   - `https://<your-app-name>.onrender.com`
3. 카카오 로그인 → Redirect URI 추가:
   - `https://<your-app-name>.onrender.com/auth/kakao/callback`

### 5. 배포 시작

1. "Create Web Service" 클릭
2. 자동으로 빌드 및 배포 시작
3. 빌드 로그 확인 (약 2-5분 소요)
4. 배포 완료 후 생성된 URL로 접속

## 배포 확인

### 접속 URL
```
https://<your-app-name>.onrender.com/login
```

### Health Check
```
https://<your-app-name>.onrender.com/health
```

## 자동 배포 설정

GitHub 저장소에 푸시하면 자동으로 재배포됩니다:

```bash
git add .
git commit -m "Update dashboard"
git push origin main
```

## 모니터링

### 로그 확인
- Render 대시보드 → Logs 탭
- 실시간 로그 스트리밍 지원

### 메트릭 확인
- Render 대시보드 → Metrics 탭
- CPU, 메모리 사용량 모니터링

## 문제 해결

### 빌드 실패
- `requirements.txt` 파일 확인
- Python 버전 호환성 확인
- 빌드 로그에서 에러 메시지 확인

### 시작 실패
- 환경 변수가 모두 설정되었는지 확인
- `gunicorn` 명령어 확인
- 포트 바인딩 확인 (Render는 자동으로 PORT 환경변수 제공)

### OAuth 로그인 실패
- 리다이렉트 URI가 정확히 일치하는지 확인
- HTTPS 프로토콜 사용 확인
- 환경 변수의 OAuth 키 확인

### 성능 이슈
- Free 플랜은 일정 시간 후 슬립 모드 진입
- 지속적인 서비스가 필요한 경우 유료 플랜 고려

## 커스텀 도메인 설정 (선택사항)

1. Render 대시보드 → Settings → Custom Domain
2. 도메인 추가 (예: `bitcoin.yourdomain.com`)
3. DNS 설정:
   - CNAME 레코드 추가
   - Target: `<your-app-name>.onrender.com`
4. SSL 인증서 자동 발급

## 비용

### Free 플랜
- 월 750시간 무료 (약 31일)
- 15분 동안 요청이 없으면 슬립 모드
- 512MB RAM
- 공유 CPU

### Starter 플랜 ($7/월)
- 24/7 가동
- 512MB RAM
- 0.5 CPU
- 자동 스케일링 없음

### 추천 설정
- 개발/테스트: Free 플랜
- 프로덕션: Starter 이상

## 보안 권장사항

1. **강력한 SECRET_KEY 사용**
   ```python
   import secrets
   secrets.token_hex(32)
   ```

2. **환경 변수로 민감정보 관리**
   - 절대 코드에 직접 키 입력 금지

3. **HTTPS 강제 사용**
   - Render는 자동으로 HTTPS 제공

4. **정기적인 키 갱신**
   - OAuth 키 주기적 갱신
   - SECRET_KEY 정기적 변경

## 지원 및 문서

- [Render 공식 문서](https://render.com/docs)
- [Python 배포 가이드](https://render.com/docs/deploy-python)
- [환경 변수 관리](https://render.com/docs/environment-variables)
- [커스텀 도메인](https://render.com/docs/custom-domains)