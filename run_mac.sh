#!/bin/bash
# ============================================================
#  Mac_MuBig_UI v2.1 실행 스크립트
#  Python 설치 없이도 자동으로 환경을 구성하고 실행합니다.
#  사용법: 이 파일을 더블클릭하거나 터미널에서 ./run_mac.sh
# ============================================================

APP_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$APP_DIR"

echo "======================================"
echo "  Mac_MuBig_UI v2.1 시작 중..."
echo "======================================"

# ── Python3 확인 ─────────────────────────────────────────────
if ! command -v python3 &> /dev/null; then
    osascript -e 'display dialog "Python3가 설치되어 있지 않습니다.\n\nhttps://www.python.org/downloads/ 에서\nPython 3.10 이상을 설치 후 다시 실행해주세요." buttons {"확인"} default button "확인" with icon stop with title "Mac_MuBig_UI"'
    exit 1
fi

PY_VER=$(python3 -c 'import sys; v=sys.version_info; print(f"{v.major}.{v.minor}")')
echo "Python $PY_VER 감지됨"

# ── 가상환경 설정 (처음 한 번만) ────────────────────────────
VENV_DIR="$APP_DIR/.venv_mubig"

if [ ! -d "$VENV_DIR" ]; then
    echo "초기 환경 설정 중... (최초 1회만 실행됩니다)"
    python3 -m venv "$VENV_DIR"
    if [ $? -ne 0 ]; then
        osascript -e 'display dialog "가상환경 생성에 실패했습니다.\nPython 버전을 확인해주세요." buttons {"확인"} default button "확인" with icon stop with title "Mac_MuBig_UI"'
        exit 1
    fi
fi

# ── 의존성 설치 (처음 한 번만) ──────────────────────────────
VENV_PY="$VENV_DIR/bin/python3"
VENV_PIP="$VENV_DIR/bin/pip3"

if [ ! -f "$VENV_DIR/.deps_installed" ]; then
    echo "필요한 패키지 설치 중... (최초 1회, 수 분 소요될 수 있습니다)"
    "$VENV_PIP" install --upgrade pip --quiet
    "$VENV_PIP" install pyside6 requests --quiet
    if [ $? -eq 0 ]; then
        touch "$VENV_DIR/.deps_installed"
        echo "패키지 설치 완료"
    else
        osascript -e 'display dialog "패키지 설치에 실패했습니다.\n인터넷 연결을 확인해주세요." buttons {"확인"} default button "확인" with icon stop with title "Mac_MuBig_UI"'
        exit 1
    fi
fi

# ── 프로그램 실행 ────────────────────────────────────────────
echo "프로그램 실행 중..."
"$VENV_PY" main.py

if [ $? -ne 0 ]; then
    osascript -e 'display dialog "프로그램 실행 중 오류가 발생했습니다." buttons {"확인"} default button "확인" with icon stop with title "Mac_MuBig_UI"'
fi
