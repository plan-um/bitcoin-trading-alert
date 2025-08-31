#!/usr/bin/env python3
"""
Render 자동 배포 스크립트
사용법: python deploy_to_render.py
"""

import os
import json
import time
import subprocess
import secrets
import webbrowser
from datetime import datetime

# Configuration
SERVICE_NAME = "bitcoin-trading-alert"
GITHUB_REPO = "https://github.com/plan-um/bitcoin-trading-alert"
RENDER_REGION = "singapore"  # oregon, frankfurt, singapore, ohio

def print_step(message):
    """단계별 메시지 출력"""
    print(f"\n{'='*60}")
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {message}")
    print('='*60)

def generate_secret_key():
    """Flask용 시크릿 키 생성"""
    return secrets.token_hex(32)

def create_render_yaml_for_dashboard():
    """대시보드용 render.yaml 생성"""
    render_config = {
        "services": [
            {
                "type": "web",
                "name": SERVICE_NAME,
                "env": "python",
                "buildCommand": "pip install -r requirements.txt",
                "startCommand": "gunicorn app_with_auth:app --bind 0.0.0.0:$PORT --timeout 120 --workers 2",
                "envVars": [
                    {"key": "PYTHON_VERSION", "value": "3.11.0"},
                    {"key": "FLASK_ENV", "value": "production"},
                    {"key": "FLASK_SECRET_KEY", "generateValue": True},
                ],
                "autoDeploy": True
            }
        ]
    }
    
    with open('render.yaml', 'w') as f:
        import yaml
        yaml.dump(render_config, f, default_flow_style=False)
    
    print("✅ render.yaml 파일이 생성되었습니다.")

def setup_oauth_instructions():
    """OAuth 설정 안내"""
    print_step("OAuth 설정 안내")
    
    print("""
📋 OAUTH 설정이 필요합니다:

1. Google OAuth 설정:
   - https://console.cloud.google.com 접속
   - 새 프로젝트 생성 또는 기존 프로젝트 선택
   - "API 및 서비스" → "사용자 인증 정보" → "OAuth 2.0 클라이언트 ID" 생성
   - 승인된 리디렉션 URI 추가:
     * https://{SERVICE_NAME}.onrender.com/auth/google/callback

2. Kakao OAuth 설정:
   - https://developers.kakao.com 접속
   - 애플리케이션 생성
   - 플랫폼 → Web 플랫폼 등록
   - 카카오 로그인 → Redirect URI 추가:
     * https://{SERVICE_NAME}.onrender.com/auth/kakao/callback

3. 환경 변수 준비:
   - GOOGLE_CLIENT_ID: Google OAuth 클라이언트 ID
   - GOOGLE_CLIENT_SECRET: Google OAuth 시크릿
   - KAKAO_CLIENT_ID: Kakao REST API 키
""".format(SERVICE_NAME=SERVICE_NAME))
    
    input("\n위 설정을 완료한 후 Enter를 누르세요...")

def create_env_file():
    """환경 변수 파일 생성"""
    print_step("환경 변수 설정")
    
    env_vars = {}
    
    # Flask Secret Key
    env_vars['FLASK_SECRET_KEY'] = generate_secret_key()
    print(f"✅ FLASK_SECRET_KEY 자동 생성됨")
    
    # Google OAuth
    print("\n🔑 Google OAuth 정보 입력:")
    env_vars['GOOGLE_CLIENT_ID'] = input("Google Client ID: ").strip()
    env_vars['GOOGLE_CLIENT_SECRET'] = input("Google Client Secret: ").strip()
    
    # Kakao OAuth
    print("\n🔑 Kakao OAuth 정보 입력:")
    env_vars['KAKAO_CLIENT_ID'] = input("Kakao REST API Key: ").strip()
    
    # Save to JSON for Render
    with open('render_env.json', 'w') as f:
        json.dump(env_vars, f, indent=2)
    
    print("\n✅ 환경 변수가 render_env.json에 저장되었습니다.")
    return env_vars

def deploy_with_render_button():
    """Deploy to Render 버튼을 통한 배포"""
    print_step("Render 배포 시작")
    
    # Create Deploy to Render button URL
    deploy_url = f"https://render.com/deploy?repo={GITHUB_REPO}"
    
    print(f"""
🚀 배포를 시작하려면 아래 URL을 브라우저에서 열어주세요:

{deploy_url}

또는 자동으로 브라우저가 열립니다...
""")
    
    # 브라우저 자동 열기
    try:
        webbrowser.open(deploy_url)
        print("✅ 브라우저가 열렸습니다.")
    except:
        print("⚠️ 브라우저를 자동으로 열 수 없습니다. 위 URL을 복사하여 접속하세요.")
    
    print("""
📝 Render 대시보드에서 다음 단계를 따르세요:

1. "Connect GitHub account" 클릭 (이미 연결된 경우 스킵)
2. 저장소 액세스 권한 부여
3. 서비스 이름 확인: {SERVICE_NAME}
4. "Create Web Service" 클릭

5. 배포 후 Environment 탭에서 환경 변수 추가:
   - FLASK_SECRET_KEY (이미 생성됨)
   - GOOGLE_CLIENT_ID
   - GOOGLE_CLIENT_SECRET
   - KAKAO_CLIENT_ID
   - REDIRECT_URI_BASE: https://{SERVICE_NAME}.onrender.com
""".format(SERVICE_NAME=SERVICE_NAME))

def create_deployment_script():
    """배포 도우미 스크립트 생성"""
    script_content = """#!/bin/bash
# Render 배포 확인 스크립트

SERVICE_NAME="bitcoin-trading-alert"
RENDER_URL="https://$SERVICE_NAME.onrender.com"

echo "🔍 배포 상태 확인 중..."
echo "URL: $RENDER_URL"

# Health check
if curl -s "$RENDER_URL/health" | grep -q "healthy"; then
    echo "✅ 서비스가 정상적으로 실행 중입니다!"
    echo "🌐 로그인 페이지: $RENDER_URL/login"
else
    echo "⏳ 아직 배포 중입니다. 잠시 후 다시 확인하세요."
fi

# Open browser
if [[ "$OSTYPE" == "darwin"* ]]; then
    open "$RENDER_URL/login"
elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
    xdg-open "$RENDER_URL/login"
fi
"""
    
    with open('check_deployment.sh', 'w') as f:
        f.write(script_content)
    
    os.chmod('check_deployment.sh', 0o755)
    print("✅ check_deployment.sh 스크립트가 생성되었습니다.")

def main():
    """메인 실행 함수"""
    print("""
╔══════════════════════════════════════════════════════════╗
║         Bitcoin Trading Alert - Render 자동 배포         ║
╚══════════════════════════════════════════════════════════╝
""")
    
    # Step 1: OAuth 설정 안내
    setup_oauth_instructions()
    
    # Step 2: 환경 변수 설정
    env_vars = create_env_file()
    
    # Step 3: 배포 스크립트 생성
    create_deployment_script()
    
    # Step 4: Render 배포
    deploy_with_render_button()
    
    print_step("배포 완료 후 확인사항")
    
    print(f"""
✅ 배포가 완료되면:

1. 배포 URL: https://{SERVICE_NAME}.onrender.com
2. 로그인 페이지: https://{SERVICE_NAME}.onrender.com/login
3. Health Check: https://{SERVICE_NAME}.onrender.com/health

📌 환경 변수 설정 확인:
   Render Dashboard → {SERVICE_NAME} → Environment

🔧 배포 상태 확인:
   ./check_deployment.sh

📚 문제 해결:
   - Logs 탭에서 에러 메시지 확인
   - 환경 변수가 모두 설정되었는지 확인
   - OAuth 리다이렉트 URI가 정확한지 확인
""")
    
    print("\n" + "="*60)
    print("배포 프로세스가 시작되었습니다!")
    print("Render 대시보드에서 진행 상황을 확인하세요.")
    print("="*60)

if __name__ == "__main__":
    main()