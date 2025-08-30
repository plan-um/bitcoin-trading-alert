# Railway 환경변수 설정 가이드

## 1. Variables 탭 찾기
Railway 대시보드에서 프로젝트 클릭 후:
- 상단 메뉴에서 **Variables** 탭 클릭
- 또는 왼쪽 사이드바에서 **Variables** 클릭

## 2. PORT 변수 확인

### 현재 PORT 변수가 있는 경우:
- `PORT = $PORT` 또는 `PORT = ${PORT}` 같이 보인다면:
  - 🗑️ 휴지통 아이콘 클릭하여 **삭제**
  
### PORT 변수가 없는 경우:
- **New Variable** 버튼 클릭
- Variable name: `PORT`
- Value: `8080`
- **Add** 클릭

## 3. 올바른 설정 예시
```
PORT = 8080
FLASK_ENV = production
```

## 4. 설정 적용
- Variables 수정 후 자동으로 재배포 시작
- 또는 **Deployments** 탭 → **Redeploy** 버튼 클릭

## 5. Settings에서 추가 설정

**Settings** 탭 → **Networking** 섹션:
- **Generate Domain** 클릭 (도메인이 없다면)
- Port가 8080으로 설정되었는지 확인

## 6. 배포 확인

**Deployments** 탭에서:
- 최신 배포 클릭
- **View Logs** 확인
- "Starting server on port 8080" 메시지 확인

## 문제 해결

### PORT 변수가 계속 $PORT로 표시되는 경우:
1. PORT 변수 완전 삭제
2. Railway가 자동으로 포트 할당하도록 방치
3. 우리 코드는 기본값 8080 사용

### 여전히 안 되는 경우:
1. 프로젝트 삭제
2. 새 프로젝트 생성
3. GitHub 저장소 다시 연결
4. PORT 변수 설정하지 않기

## 스크린샷 위치 안내

Railway 대시보드 구조:
```
┌─────────────────────────────────────┐
│  Project Name                       │
├─────────────────────────────────────┤
│ Deployments | Variables | Settings  │
├─────────────────────────────────────┤
│                                     │
│  [New Variable]                     │
│                                     │
│  PORT         = 8080       [🗑️]    │
│  FLASK_ENV    = production [🗑️]    │
│                                     │
└─────────────────────────────────────┘
```