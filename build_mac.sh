#!/bin/bash
# ============================================================
#  Mac_MuBig_UI v2.4 macOS 빌드 스크립트
#  요구사항: Python 3.10+ (64-bit), pip
#  실행: chmod +x build_mac.sh && ./build_mac.sh
# ============================================================

APP_NAME="Mac_MuBig_UI v2.4"

echo "=== Mac_MuBig_UI v2.4 macOS 빌드 시작 ==="

# Python 확인
if ! command -v python3 &> /dev/null; then
    echo "[오류] python3 를 찾을 수 없습니다."
    echo "https://www.python.org/downloads/ 에서 설치하세요."
    exit 1
fi

echo "Python 버전: $(python3 --version)"

# 의존성 설치
echo ""
echo "의존성 설치 중..."
pip3 install --upgrade pyinstaller pyside6 requests

# 빌드
echo ""
echo "앱 빌드 중..."
pyinstaller \
    --noconfirm \
    --onedir \
    --windowed \
    --name "Mac_MuBig_UI v2.4" \
    --icon "asset/logo/Mubig.icns" \
    --add-data "asset:asset" \
    --add-data "MuBig_config.json:." \
    --hidden-import "PySide6.QtCore" \
    --hidden-import "PySide6.QtGui" \
    --hidden-import "PySide6.QtWidgets" \
    --hidden-import "PySide6.QtNetwork" \
    --hidden-import "requests" \
    --hidden-import "src" \
    --hidden-import "src.auth" \
    --hidden-import "src.installer" \
    --hidden-import "src.settings" \
    --hidden-import "src.ui" \
    --hidden-import "src.ui.main_window" \
    --hidden-import "src.ui.install_tab" \
    --hidden-import "src.ui.settings_tab" \
    --hidden-import "src.ui.custom_widgets" \
    --hidden-import "src.ui.styles" \
    --hidden-import "src.ui.wtf_file_dialog" \
    --hidden-import "src.utils" \
    --hidden-import "src.utils.file_handler" \
    --hidden-import "src.utils.game_paths" \
    main.py

if [ $? -eq 0 ]; then
    echo ""
    echo "=== 빌드 성공 ==="
    echo "결과물: dist/Mac_MuBig_UI v2.4.app"
    echo ""
    echo "압축하려면:"
    echo "   cd dist && zip -r 'Mac_MuBig_UI_v2.4.zip' 'Mac_MuBig_UI v2.4.app'"
    echo ""
    echo "※ macOS Gatekeeper 서명 없이 배포할 경우 사용자가 아래 명령 실행 필요:"
    echo "   xattr -cr \"/Applications/Mac_MuBig_UI v2.4.app\""
else
    echo ""
    echo "=== 빌드 실패 ==="
    exit 1
fi
