"""
메인 윈도우
어플리케이션의 메인 윈도우 구현
"""

import sys
import os
import platform
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QTabWidget, QPushButton, QLabel, QMessageBox,
    QInputDialog, QLineEdit, QDialog, QVBoxLayout as QVBox,
    QRadioButton, QDialogButtonBox
)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QIcon
from .custom_widgets import OutlinedButton
from .install_tab import InstallTab
from .settings_tab import SettingsTab
from .styles import APP_STYLESHEET
from ..auth import AuthManager
from ..utils.game_paths import find_wow_installation_paths, GAME_VERSIONS, VERSION_ORDER



class MainWindow(QMainWindow):
    """메인 윈도우 클래스"""

    def __init__(self, settings, dev_mode=False):
        super().__init__()
        self.settings = settings
        self.dev_mode = dev_mode
        self.auth_manager = AuthManager(settings)
        self.setup_ui()

        if not self.dev_mode:
            QTimer.singleShot(100, self._startup_auto_detect)
        else:
            self.update_auth_status(True)

    def _startup_auto_detect(self):
        """프로그램 시작 시 게임 경로 자동 탐색 (미설정 버전만)"""
        needs = any(not self.settings.get_game_path(k) for k in VERSION_ORDER)
        if needs:
            found = find_wow_installation_paths()
            for key, path in found.items():
                if not self.settings.get_game_path(key):
                    self.settings.set_game_path(key, path)
            self.settings_tab._on_version_combo_changed(
                self.settings_tab.version_combo.currentIndex()
            )
        self.check_authentication()

    def setup_ui(self):
        """UI 초기화"""
        if platform.system() == 'Darwin':
            self.setWindowTitle('Mac_MuBig_UI 설치 프로그램 v2.4')
        else:
            self.setWindowTitle('MuBig_UI 설치 프로그램 v2.4')
        self.setMinimumSize(700, 500)

        _base = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        _icon_file = 'Mubig.icns' if platform.system() == 'Darwin' else 'Mubig.ico'
        icon_path = os.path.join(_base, 'asset', 'logo', _icon_file)
        # fallback: ICO works on both platforms if ICNS absent
        if not os.path.exists(icon_path):
            icon_path = os.path.join(_base, 'asset', 'logo', 'Mubig.ico')
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))

        self.setStyleSheet(APP_STYLESHEET)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(5, 5, 5, 5)

        self.tab_widget = QTabWidget()

        button_widget = QWidget()
        button_layout = QHBoxLayout(button_widget)
        button_layout.setContentsMargins(0, 0, 0, 0)
        button_layout.setSpacing(5)

        self.version_button = OutlinedButton(self.get_current_version_name())
        self.version_button.setProperty('class', 'version-button')
        self.version_button.clicked.connect(self.select_game_version)
        self.version_button.setMinimumHeight(25)
        self.version_button.setFixedWidth(120)
        self._update_version_button_color()

        self.auth_button = OutlinedButton('인증')
        self.auth_button.setProperty('class', 'auth-button')
        self.auth_button.clicked.connect(self.authenticate)
        self.auth_button.setMinimumHeight(25)
        self.auth_button.setFixedWidth(80)
        self.auth_button.setNormalColor('#ff1600')

        # UI 다운로드 버튼 (버전 버튼 왼쪽)
        self.ui_download_btn = OutlinedButton('UI 다운로드')
        self.ui_download_btn.setMinimumHeight(25)
        self.ui_download_btn.setFixedWidth(110)
        self.ui_download_btn.setToolTip('선택한 버전의 UI를 다운로드 합니다')
        self.ui_download_btn.clicked.connect(self._on_ui_download_clicked)
        self.ui_download_btn.setEnabled(False)  # 인증 전 비활성화

        button_layout.addWidget(self.ui_download_btn)
        button_layout.addWidget(self.version_button)
        button_layout.addWidget(self.auth_button)

        self.tab_widget.setCornerWidget(button_widget, Qt.TopRightCorner)

        self.install_tab = InstallTab(self.settings, self.auth_manager, self.dev_mode)
        self.tab_widget.addTab(self.install_tab, '설치')

        self.settings_tab = SettingsTab(self.settings)
        self.tab_widget.addTab(self.settings_tab, '설정')

        self.tab_widget.currentChanged.connect(self.on_tab_changed)
        main_layout.addWidget(self.tab_widget)

    def check_authentication(self):
        """저장된 패스워드로 자동 재인증"""
        saved_password = self.settings.get('auth', 'auth_url', default='')
        if saved_password:
            success, message = self.auth_manager.authenticate(saved_password)
            if success:
                self.update_auth_status(True)
            else:
                self.auth_manager.reset_authentication()
                self.update_auth_status(False)
                QMessageBox.warning(self, '인증 실패',
                    '저장된 인증 정보가 유효하지 않습니다.\n다시 인증해주세요.')
        else:
            self.update_auth_status(False)

    def update_auth_status(self, authenticated: bool):
        if authenticated:
            self.auth_button.setText('인증완료')
            self.auth_button.setNormalColor('#25e649')
            self.install_tab.enable_buttons(True)
            self.ui_download_btn.setEnabled(True)
        else:
            self.auth_button.setText('인증')
            self.auth_button.setNormalColor('#ff1600')
            self.install_tab.enable_buttons(False)
            self.ui_download_btn.setEnabled(False)

    def authenticate(self):
        if self.dev_mode:
            QMessageBox.information(self, '개발모드', '개발모드에서는 인증이 필요하지 않습니다.')
            return

        password_dialog = QInputDialog(self)
        password_dialog.setWindowTitle('인증')
        password_dialog.setLabelText('패스워드를 입력하세요:')
        password_dialog.setTextEchoMode(QLineEdit.Password)
        password_dialog.setOkButtonText('확인')
        password_dialog.setCancelButtonText('취소')
        password_dialog.resize(350, 120)

        ok = password_dialog.exec()
        password = password_dialog.textValue()

        if ok and password:
            success, message = self.auth_manager.authenticate(password.strip())
            if success:
                self.update_auth_status(True)
                QMessageBox.information(self, '인증 성공', '인증이 완료되었습니다.')
            else:
                self.update_auth_status(False)
                QMessageBox.warning(self, '인증 실패', message)

    def select_game_version(self):
        dialog = QDialog(self)
        dialog.setWindowTitle('게임 버전 선택')
        dialog.setMinimumWidth(300)
        layout = QVBox()
        current_version = self.settings.get_selected_version()
        radio_buttons = {}

        for key in VERSION_ORDER:
            name = self.settings.get_game_version_name(key)
            path = self.settings.get_game_path(key)
            path_display = path if path else '경로 미설정'
            radio = QRadioButton(f'{name} - {path_display}')
            radio.setChecked(key == current_version)
            radio_buttons[key] = radio
            layout.addWidget(radio)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addWidget(buttons)
        dialog.setLayout(layout)

        if dialog.exec() == QDialog.Accepted:
            for key, radio in radio_buttons.items():
                if radio.isChecked():
                    self.settings.set_selected_version(key)
                    self.version_button.setText(self.get_current_version_name())
                    self._update_version_button_color()
                    break


    # 게임 버전별 기본 배경색 (hover 효과는 OutlinedButton 자체 처리)
    _VERSION_BG = {
        'retail':      '#b38aff',
        'classic':     '#36ffc8',
        'anniversary': '#ff8a48',
        'classic_era': '#fff058',
    'forever':     '#ff6eb4',   # 포에버 — 핑크
    }

    def _on_ui_download_clicked(self):
        """UI 다운로드 버튼 클릭 → install_tab 의 download_ui 위임"""
        self.install_tab.download_ui()

    def _update_version_button_color(self):
        """현재 선택 버전에 맞는 버튼 배경색 적용"""
        version = self.settings.get_selected_version()
        bg = self._VERSION_BG.get(version, '#4a9eff')
        self.version_button.setNormalColor(bg)

    def get_current_version_name(self) -> str:
        version = self.settings.get_selected_version()
        return self.settings.get_game_version_name(version)

    def on_tab_changed(self, index):
        pass

    def closeEvent(self, event):
        self.settings.save_config()
        event.accept()
