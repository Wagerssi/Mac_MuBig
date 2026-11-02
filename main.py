"""
Mubig_UI 멤버십 프로그램
World of Warcraft UI 설치 및 관리 프로그램
"""

import sys
import os
import json
from pathlib import Path
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt, QTranslator, QLibraryInfo
from PySide6.QtGui import QIcon

from src.ui.main_window import MainWindow
from src.settings import Settings


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("Mubig")
    app.setOrganizationName("Mubig")

    # 아이콘 설정
    icon_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'asset', 'logo', 'Mubig.ico')
    if os.path.exists(icon_path):
        app.setWindowIcon(QIcon(icon_path))

    # 번역 설정 (한국어)
    translator = QTranslator()
    qt_translations_path = QLibraryInfo.path(QLibraryInfo.TranslationsPath)
    translator.load("qtbase_ko", qt_translations_path)
    app.installTranslator(translator)

    # 개발 모드 확인
    dev_mode = os.environ.get("DEV_MODE", "").lower() == "true" or "--dev" in sys.argv
    if dev_mode:
        print("*** 개발모드로 실행 중 - 인증 비활성화 ***")

    settings = Settings()
    window = MainWindow(settings, dev_mode)
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
