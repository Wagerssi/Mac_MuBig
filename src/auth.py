"""
MuBig_UI 인증 관리 모듈
Google Apps Script 서버를 통해 인증 및 다운로드 링크 조회
"""

import requests
from typing import Optional, Tuple

# =====================================================================
# ★ 설정: Google Apps Script 웹앱 URL 을 아래에 입력하세요 ★
# Apps Script 배포 후 받은 URL
# (예: https://script.google.com/macros/s/XXXX/exec)
# =====================================================================
AUTH_SERVER_URL = "https://cool-dew-5c25.mr-wager80.workers.dev"
# =====================================================================


class AuthManager:
    """Google Apps Script 서버 기반 인증 관리"""

    def __init__(self, settings):
        self.settings = settings
        self.is_authenticated = settings.is_authenticated()

    # ── 서버 요청 공통 ────────────────────────────────────────────
    def _post(self, payload: dict, timeout: int = 10) -> Optional[dict]:
        try:
            resp = requests.post(
                AUTH_SERVER_URL,
                json=payload,
                timeout=timeout,
                allow_redirects=True
            )
            if resp.status_code != 200:
                return None
            return resp.json()
        except requests.exceptions.Timeout:
            return {"valid": False, "message": "서버 응답 시간 초과.\n인터넷 연결을 확인해주세요."}
        except requests.exceptions.ConnectionError:
            return {"valid": False, "message": "서버에 연결할 수 없습니다.\n인터넷 연결을 확인해주세요."}
        except Exception as e:
            return {"valid": False, "message": f"오류: {str(e)}"}

    # ── 암호 인증 ─────────────────────────────────────────────────
    def authenticate(self, password: str) -> Tuple[bool, str]:
        if not password or not password.strip():
            return False, "패스워드를 입력해주세요."

        password = password.strip()
        result = self._post({"action": "verify", "code": password})

        if result is None:
            return False, "인증 서버에 연결할 수 없습니다.\n인터넷 연결을 확인해주세요."

        valid   = result.get("valid", False)
        message = result.get("message", "")

        if valid:
            self.settings.set_authenticated(True, password)
            self.is_authenticated = True

        return valid, message

    # ── 재인증: 프로그램 시작 시 저장된 암호를 서버에서 재검증 ────
    def verify_authentication(self) -> bool:
        """
        저장된 암호를 서버에서 다시 확인
        관리자가 암호를 변경하면 다음 실행 시 자동 차단
        """
        if not self.is_authenticated:
            return False

        saved_code = self.settings.get("auth", "auth_url", default="")
        if not saved_code:
            return False

        result = self._post({"action": "verify", "code": saved_code})
        valid  = result.get("valid", False) if result else False

        if not valid:
            self.reset_authentication()
        return valid

    # ── 다운로드 링크 조회 ────────────────────────────────────────
    def fetch_config_from_drive(self) -> Optional[dict]:
        """
        서버에서 다운로드 링크를 가져옴
        관리자가 스프레드시트에서 링크를 수정하면 즉시 반영
        """
        result = self._post({"action": "downloads"})
        if not result or not result.get("valid"):
            return None
        return {
            "passwords": [],
            "downloads": result.get("downloads", {})
        }

    def reset_authentication(self):
        self.settings.set_authenticated(False, "")
        self.is_authenticated = False
