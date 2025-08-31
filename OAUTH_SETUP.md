# OAuth 로그인 설정 가이드

## 구글 OAuth 2.0 설정

### 1. Google Cloud Console 설정
1. [Google Cloud Console](https://console.cloud.google.com/) 접속
2. 새 프로젝트 생성 또는 기존 프로젝트 선택
3. "API 및 서비스" → "사용자 인증 정보" 이동
4. "사용자 인증 정보 만들기" → "OAuth 클라이언트 ID" 선택

### 2. OAuth 동의 화면 구성
- 애플리케이션 이름: Bitcoin Strategy Dashboard
- 사용자 지원 이메일: 본인 이메일
- 승인된 도메인: railway.app (프로덕션용)
- 개발자 연락처 정보 입력

### 3. OAuth 2.0 클라이언트 ID 생성
- 애플리케이션 유형: 웹 애플리케이션
- 이름: Bitcoin Dashboard OAuth
- 승인된 JavaScript 원본:
  - `http://localhost:8080`
  - `https://bitcoin-trading-alert-production.up.railway.app`
- 승인된 리디렉션 URI:
  - `http://localhost:8080/auth/google/callback`
  - `https://bitcoin-trading-alert-production.up.railway.app/auth/google/callback`

### 4. 클라이언트 ID 및 시크릿 저장
생성된 클라이언트 ID와 시크릿을 `.env` 파일에 저장

---

## 카카오 OAuth 2.0 설정

### 1. Kakao Developers 설정
1. [Kakao Developers](https://developers.kakao.com/) 접속
2. "내 애플리케이션" → "애플리케이션 추가하기"
3. 앱 이름: Bitcoin Strategy Dashboard
4. 사업자명: 개인 또는 회사명

### 2. 앱 설정
1. "앱 설정" → "플랫폼" → "Web 플랫폼 등록"
   - 사이트 도메인:
     - `http://localhost:8080`
     - `https://bitcoin-trading-alert-production.up.railway.app`

2. "제품 설정" → "카카오 로그인" 활성화
3. "카카오 로그인" → "Redirect URI 등록"
   - `http://localhost:8080/auth/kakao/callback`
   - `https://bitcoin-trading-alert-production.up.railway.app/auth/kakao/callback`

### 3. 동의 항목 설정
"카카오 로그인" → "동의항목"에서 다음 항목 설정:
- 프로필 정보(닉네임/프로필 사진): 필수 동의
- 카카오계정(이메일): 선택 동의

### 4. 앱 키 저장
"앱 설정" → "앱 키"에서 REST API 키를 `.env` 파일에 저장

---

## 환경 변수 설정

### 1. `.env` 파일 생성
```bash
cp .env.example .env
```

### 2. `.env` 파일 편집
```env
# Flask 설정
FLASK_SECRET_KEY=your-secret-key-here-change-in-production
FLASK_ENV=development

# Google OAuth 2.0 설정
GOOGLE_CLIENT_ID=your-google-client-id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your-google-client-secret

# Kakao OAuth 2.0 설정
KAKAO_CLIENT_ID=your-kakao-rest-api-key
KAKAO_CLIENT_SECRET=your-kakao-client-secret  # Optional

# 리다이렉트 URL (개발/프로덕션 환경에 맞게 수정)
REDIRECT_URI_BASE=http://localhost:8080
```

### 3. Railway 환경 변수 설정
Railway 대시보드에서 다음 환경 변수 추가:
- `FLASK_SECRET_KEY`: 안전한 랜덤 키 생성
- `FLASK_ENV`: production
- `GOOGLE_CLIENT_ID`: Google OAuth 클라이언트 ID
- `GOOGLE_CLIENT_SECRET`: Google OAuth 시크릿
- `KAKAO_CLIENT_ID`: Kakao REST API 키
- `REDIRECT_URI_BASE`: https://bitcoin-trading-alert-production.up.railway.app

---

## 로컬 테스트

### 1. 패키지 설치
```bash
pip install -r requirements.txt
```

### 2. 앱 실행
```bash
python app_with_auth.py
```

### 3. 브라우저에서 접속
```
http://localhost:8080/login
```

---

## 보안 주의사항

1. **절대 `.env` 파일을 Git에 커밋하지 마세요**
2. **프로덕션 환경에서는 강력한 SECRET_KEY 사용**
3. **HTTPS 사용 필수 (Railway는 자동 제공)**
4. **정기적으로 OAuth 키 갱신**

---

## 문제 해결

### Google 로그인 오류
- 리디렉션 URI가 정확히 일치하는지 확인
- Google Cloud Console에서 OAuth 동의 화면이 구성되었는지 확인
- 테스트 사용자로 추가되었는지 확인 (개발 모드)

### Kakao 로그인 오류
- 플랫폼 도메인이 정확히 등록되었는지 확인
- Redirect URI가 정확히 일치하는지 확인
- 카카오 로그인이 활성화되었는지 확인

### Railway 배포 오류
- 환경 변수가 모두 설정되었는지 확인
- REDIRECT_URI_BASE가 프로덕션 URL로 설정되었는지 확인
- requirements.txt에 모든 패키지가 포함되었는지 확인