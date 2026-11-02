"""
설치 탭
Mubig_UI 설치 관련 기능 구현
"""

import os
import webbrowser
from pathlib import Path
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QLabel, QProgressBar, QTextEdit, QGroupBox,
    QFileDialog, QMessageBox, QDialog
)
from PySide6.QtCore import Qt, Signal, QThread
from .custom_widgets import OutlinedButton

from ..installer import Installer

def _get_download_folder() -> str:
    """OS별 다운로드 폴더 경로 반환"""
    import platform, os
    system = platform.system()

    if system == 'Windows':
        try:
            import struct, ctypes
            guid = struct.pack('<IHH8B',
                0x374DE290, 0x123F, 0x4565,
                0x91, 0x64, 0x39, 0xC4, 0x92, 0x5E, 0x46, 0x7B)
            path_ptr = ctypes.c_wchar_p()
            ret = ctypes.windll.shell32.SHGetKnownFolderPath(
                guid, 0, None, ctypes.byref(path_ptr))
            if ret == 0 and path_ptr.value:
                result = path_ptr.value
                ctypes.windll.ole32.CoTaskMemFree(path_ptr)
                return result
        except Exception:
            pass
        return os.path.join(os.path.expanduser('~'), 'Downloads')

    elif system == 'Darwin':  # macOS
        return os.path.join(os.path.expanduser('~'), 'Downloads')

    else:  # Linux 등
        return os.path.join(os.path.expanduser('~'), 'Downloads')


class DownloadLinkWorker(QThread):
    """구글드라이브에서 다운로드 링크를 비동기로 가져오는 워커"""
    result_signal = Signal(object)   # cfg dict or None

    def __init__(self, auth_manager):
        super().__init__()
        self.auth_manager = auth_manager

    def run(self):
        try:
            cfg = self.auth_manager.fetch_config_from_drive()
            self.result_signal.emit(cfg)
        except Exception:
            self.result_signal.emit(None)

class BackupWorker(QThread):
    """백업 작업을 백그라운드에서 수행하는 워커 스레드"""
    progress_signal = Signal(int)
    log_signal = Signal(str)
    finished_signal = Signal(bool, str)

    def __init__(self, game_path: str, out_path: str):
        super().__init__()
        self.game_path = game_path
        self.out_path = out_path

    def run(self):
        import zipfile, os
        try:
            folders = ['Fonts', 'Interface', 'WTF']
            base = Path(self.game_path)

            # 총 파일 수 계산
            total = 0
            for folder in folders:
                fp = base / folder
                if fp.exists():
                    for _ in fp.rglob('*'):
                        total += 1

            if total == 0:
                self.finished_signal.emit(False, "백업할 파일이 없습니다.")
                return

            done = 0
            with zipfile.ZipFile(self.out_path, 'w', zipfile.ZIP_DEFLATED) as zf:
                for folder in folders:
                    fp = base / folder
                    if not fp.exists():
                        self.log_signal.emit(f"  [{folder}] 폴더 없음, 건너뜀")
                        continue
                    self.log_signal.emit(f"  [{folder}] 압축 중...")
                    for file in fp.rglob('*'):
                        if file.is_file():
                            arcname = file.relative_to(base)
                            zf.write(file, arcname)
                            done += 1
                            self.progress_signal.emit(int(done / total * 100))

            self.finished_signal.emit(True, "완료")
        except Exception as e:
            self.finished_signal.emit(False, str(e))

class InstallWorker(QThread):
    """설치 작업을 백그라운드에서 수행하는 워커 스레드"""

    progress_signal = Signal(int)
    log_signal = Signal(str)
    finished_signal = Signal(bool, str)

    def __init__(self, installer, install_type, **kwargs):
        super().__init__()
        self.installer = installer
        self.install_type = install_type
        self.kwargs = kwargs

    def run(self):
        """스레드 실행"""
        try:
            success = False

            if self.install_type == "full":
                success = self.installer.full_install(
                    self.kwargs['zip_path'],
                    progress_callback=self.progress_signal.emit,
                    log_callback=self.log_signal.emit
                )
            elif self.install_type == "interface":
                success = self.installer.install_interface(
                    self.kwargs['zip_path'],
                    progress_callback=self.progress_signal.emit,
                    log_callback=self.log_signal.emit
                )
            elif self.install_type == "wtf":
                success = self.installer.install_wtf(
                    self.kwargs['zip_path'],
                    self.kwargs['selected_files'],
                    progress_callback=self.progress_signal.emit,
                    log_callback=self.log_signal.emit
                )

            if success:
                self.finished_signal.emit(True, "설치 완료")
            else:
                self.finished_signal.emit(False, "설치 중 오류가 발생했습니다.")

        except Exception as e:
            self.finished_signal.emit(False, str(e))

class InstallTab(QWidget):
    """설치 탭 위젯"""

    install_started = Signal()
    install_completed = Signal()
    install_failed = Signal(str)

    def __init__(self, settings, auth_manager, dev_mode=False):
        super().__init__()
        self.settings = settings
        self.auth_manager = auth_manager
        self.dev_mode = dev_mode
        self.installer = Installer(settings)
        self.worker = None  # 설치 워커 스레드
        self.setup_ui()

    def setup_ui(self):
        """UI 초기화"""
        layout = QVBoxLayout()
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(10)

        # 전체 설치 섹션
        self.create_full_install_section(layout)

        # 부분 설치 섹션
        self.create_partial_install_section(layout)

        # 진행 상태 섹션
        self.create_progress_section(layout)

        self.setLayout(layout)

    def create_full_install_section(self, parent_layout):
        """전체 설치 섹션 생성"""
        group = QGroupBox("Mubig_UI")
        layout = QHBoxLayout()
        layout.setSpacing(10)

        self.full_install_btn = OutlinedButton("전체 설치")
        self.full_install_btn.setMinimumHeight(45)
        self.full_install_btn.setStyleSheet("QPushButton { font-size: 14px; font-weight: bold; }")
        self.full_install_btn.clicked.connect(self.full_install)

        self.full_backup_btn = OutlinedButton("전체 백업")
        self.full_backup_btn.setMinimumHeight(45)
        self.full_backup_btn.setStyleSheet("QPushButton { font-size: 14px; font-weight: bold; }")
        self.full_backup_btn.clicked.connect(self.full_backup)

        layout.addWidget(self.full_install_btn)
        layout.addWidget(self.full_backup_btn)
        group.setLayout(layout)
        parent_layout.addWidget(group)
    def create_partial_install_section(self, parent_layout):
        """부분 설치 섹션 생성"""
        group = QGroupBox("Mubig_UI 부분 설치")
        layout = QHBoxLayout()
        layout.setSpacing(10)

        # Interface 버튼
        self.interface_btn = OutlinedButton("INTERFACE")
        self.interface_btn.setMinimumHeight(45)
        self.interface_btn.setStyleSheet("""
            QPushButton {
                font-size: 14px;
                font-weight: bold;
            }
        """)
        self.interface_btn.clicked.connect(self.install_interface)

        # WTF 버튼
        self.wtf_btn = OutlinedButton("WTF")
        self.wtf_btn.setMinimumHeight(45)
        self.wtf_btn.setStyleSheet("""
            QPushButton {
                font-size: 14px;
                font-weight: bold;
            }
        """)
        self.wtf_btn.clicked.connect(self.install_wtf)

        layout.addWidget(self.interface_btn)
        layout.addWidget(self.wtf_btn)

        group.setLayout(layout)
        parent_layout.addWidget(group)

    def create_progress_section(self, parent_layout):
        """진행 상태 섹션 생성"""
        group = QGroupBox("진행 상태")
        layout = QVBoxLayout()

        # 진행률 바
        self.progress_bar = QProgressBar()
        self.progress_bar.setMinimum(0)
        self.progress_bar.setMaximum(100)
        self.progress_bar.setValue(0)

        # 로그 텍스트
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setMinimumHeight(150)

        layout.addWidget(self.progress_bar)
        layout.addWidget(QLabel("로그:"))
        layout.addWidget(self.log_text, 1)  # stretch factor 1

        group.setLayout(layout)
        parent_layout.addWidget(group, 1)  # stretch factor 1

    def enable_buttons(self, enabled: bool):
        """버튼 활성화/비활성화"""
        self.full_install_btn.setEnabled(enabled)
        self.full_backup_btn.setEnabled(enabled)
        self.interface_btn.setEnabled(enabled)
        self.wtf_btn.setEnabled(enabled)

    def log_message(self, message: str):
        """로그 메시지 추가"""
        self.log_text.append(message)

    def update_progress(self, value: int):
        """진행률 업데이트"""
        self.progress_bar.setValue(value)

    def download_ui(self):
        """현재 선택된 게임버전의 UI를 구글드라이브에서 다운로드 (비동기)"""
        self.log_message("다운로드 링크 조회 중...")
        self._download_link_worker = DownloadLinkWorker(self.auth_manager)
        self._download_link_worker.result_signal.connect(self._on_download_link_received)
        self._download_link_worker.start()

    def _on_download_link_received(self, cfg):
        """다운로드 링크 조회 완료 콜백"""
        version = self.settings.get_selected_version()

        if not cfg:
            QMessageBox.warning(self, "연결 실패",
                "서버에 연결할 수 없습니다.\n인터넷 연결을 확인해주세요.")
            return

        downloads = cfg.get("downloads", {})
        url = downloads.get(version)

        if not url:
            from ..utils.game_paths import GAME_VERSIONS
            vname = GAME_VERSIONS.get(version, {}).get("name", version)
            QMessageBox.information(self, "다운로드 링크 없음",
                f"{vname} 버전의 다운로드 링크가 등록되어 있지 않습니다.")
            return

        # 구글드라이브 공유링크 → 직접 다운로드 URL 변환
        import re
        from ..utils.game_paths import GAME_VERSIONS
        file_id_match = re.search(r'/file/d/([a-zA-Z0-9-_]+)', url)
        if file_id_match:
            file_id = file_id_match.group(1)
            open_url = f"https://drive.google.com/uc?id={file_id}&export=download"
        else:
            open_url = url

        vname = GAME_VERSIONS.get(version, {}).get("name", version)
        self.log_message(f"[{vname}] UI 다운로드 링크를 브라우저에서 엽니다...")
        webbrowser.open(open_url)


    def full_install(self):
        """전체 설치 실행"""
        # 인증 확인 (개발모드가 아닐 때만)
        if not self.dev_mode and not self.auth_manager.is_authenticated:
            QMessageBox.warning(self, "인증 필요", "먼저 인증을 완료해 주세요.")
            return

        # 게임 경로 확인
        version = self.settings.get_selected_version()
        game_path = self.settings.get_game_path(version)

        if not game_path:
            QMessageBox.warning(self, "경로 미설정",
                              f"{self.settings.get_game_version_name(version)} 경로가 설정되지 않았습니다.\n설정 탭에서 경로를 지정해 주세요.")
            return

        # 압축 파일 선택
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Mubig_UI 압축 파일 선택",
            _get_download_folder(),
            "ZIP Files (*.zip)"
        )

        if not file_path:
            return

        # 경고 메시지
        reply = QMessageBox.warning(
            self,
            "전체 설치 경고",
            "전체 설치시 기존에 사용중인 설정값은 삭제됩니다.\n계속하시겠습니까?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if reply == QMessageBox.No:
            return

        # 설치 시작
        self.install_started.emit()
        self.log_message("===== 전체 설치 시작 =====")
        self.log_message(f"선택된 파일: {file_path}")
        self.log_message(f"설치 경로: {game_path}")

        # 설치 버튼 비활성화
        self.enable_buttons(False)

        # 워커 스레드 생성 및 실행
        self.worker = InstallWorker(self.installer, "full", zip_path=file_path)
        self.worker.progress_signal.connect(self.update_progress)
        self.worker.log_signal.connect(self.log_message)
        self.worker.finished_signal.connect(lambda success, msg: self.on_install_finished(success, msg, "전체"))
        self.worker.start()

    def install_interface(self):
        """Interface 부분 설치"""
        # 인증 확인 (개발모드가 아닐 때만)
        if not self.dev_mode and not self.auth_manager.is_authenticated:
            QMessageBox.warning(self, "인증 필요", "먼저 인증을 완료해 주세요.")
            return

        # 게임 경로 확인
        version = self.settings.get_selected_version()
        game_path = self.settings.get_game_path(version)

        if not game_path:
            QMessageBox.warning(self, "경로 미설정",
                              f"{self.settings.get_game_version_name(version)} 경로가 설정되지 않았습니다.\n설정 탭에서 경로를 지정해 주세요.")
            return

        # 압축 파일 선택
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Mubig_UI 압축 파일 선택",
            _get_download_folder(),
            "ZIP Files (*.zip)"
        )

        if not file_path:
            return

        # 경고 메시지
        reply = QMessageBox.warning(
            self,
            "Interface 설치 확인",
            "사용중인 애드온만 업데이트하며 UI 설정값은 변경 되지 않습니다.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if reply == QMessageBox.No:
            return

        # 설치 시작
        self.log_message("===== Interface 부분 설치 시작 =====")
        self.log_message(f"선택된 파일: {file_path}")

        # 설치 버튼 비활성화
        self.enable_buttons(False)

        # 워커 스레드 생성 및 실행
        self.worker = InstallWorker(self.installer, "interface", zip_path=file_path)
        self.worker.progress_signal.connect(self.update_progress)
        self.worker.log_signal.connect(self.log_message)
        self.worker.finished_signal.connect(lambda success, msg: self.on_install_finished(success, msg, "Interface"))
        self.worker.start()

    def install_wtf(self):
        """WTF 부분 설치"""
        # 인증 확인 (개발모드가 아닐 때만)
        if not self.dev_mode and not self.auth_manager.is_authenticated:
            QMessageBox.warning(self, "인증 필요", "먼저 인증을 완료해 주세요.")
            return

        # 게임 경로 확인
        version = self.settings.get_selected_version()
        game_path = self.settings.get_game_path(version)

        if not game_path:
            QMessageBox.warning(self, "경로 미설정",
                              f"{self.settings.get_game_version_name(version)} 경로가 설정되지 않았습니다.\n설정 탭에서 경로를 지정해 주세요.")
            return

        # 계정명 확인
        account_name = self.settings.get_account_name()
        if not account_name:
            QMessageBox.warning(self, "계정명 미설정",
                              "계정명이 설정되지 않았습니다.\n설정 탭에서 계정명을 입력해 주세요.")
            return

        # 압축 파일 선택
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Mubig_UI 압축 파일 선택",
            _get_download_folder(),
            "ZIP Files (*.zip)"
        )

        if not file_path:
            return

        # WTF 파일 선택 다이얼로그 (별도 구현 필요)
        from .wtf_file_dialog import WTFFileDialog
        dialog = WTFFileDialog(file_path, self)
        if dialog.exec() != QDialog.Accepted:
            return

        selected_files = dialog.get_selected_files()
        if not selected_files:
            QMessageBox.warning(self, "파일 미선택", "설치할 파일을 선택해 주세요.")
            return

        # 설치 시작
        self.log_message("===== WTF 부분 설치 시작 =====")
        self.log_message(f"선택된 파일: {len(selected_files)}개")

        # 설치 버튼 비활성화
        self.enable_buttons(False)

        # 워커 스레드 생성 및 실행
        self.worker = InstallWorker(self.installer, "wtf", zip_path=file_path, selected_files=selected_files)
        self.worker.progress_signal.connect(self.update_progress)
        self.worker.log_signal.connect(self.log_message)
        self.worker.finished_signal.connect(lambda success, msg: self.on_install_finished(success, msg, "WTF"))
        self.worker.start()


    def full_backup(self):
        """전체 백업 실행"""
        version = self.settings.get_selected_version()
        game_path = self.settings.get_game_path(version)

        if not game_path:
            QMessageBox.warning(self, "경로 미설정",
                f"{self.settings.get_game_version_name(version)} 경로가 설정되지 않았습니다.\n설정 탭에서 경로를 지정해 주세요.")
            return

        # 확인 팝업
        reply = QMessageBox.question(
            self, "전체 백업",
            "사용중인 애드온 및 설정값 전체를 백업 합니다.\n\n계속하시겠습니까?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        if reply != QMessageBox.Yes:
            return

        # 백업 폴더 결정 (설정에 지정된 폴더 or WoW 루트 폴더)
        backup_dir = self.settings.get_backup_save_folder()
        if not backup_dir or not Path(backup_dir).exists():
            # WoW 루트(game_path 의 상위 상위) 폴더
            wow_root = str(Path(game_path).parent)
            backup_dir = wow_root

        # 버전별 파일명 접두사
        prefix_map = {
            'retail':      'Retail',
            'classic':     'Classic',
            'anniversary': 'Anniversary',
            'classic_era': 'Era',
            'forever':     'Forever',
        }
        prefix = prefix_map.get(version, 'Backup')
        from datetime import datetime
        date_str = datetime.now().strftime('%m%d')
        base_name = f'{prefix}_{date_str}'

        # 동일 파일명 충돌 처리
        out_path = Path(backup_dir) / f'{base_name}.zip'
        counter = 1
        while out_path.exists():
            out_path = Path(backup_dir) / f'{base_name} ({counter}).zip'
            counter += 1

        # 백업 실행 (워커 스레드)
        self.enable_buttons(False)
        self.log_message("===== 전체 백업 시작 =====")
        self.log_message(f"대상 경로: {game_path}")
        self.log_message(f"저장 위치: {out_path}")

        self.worker = BackupWorker(game_path, str(out_path))
        self.worker.progress_signal.connect(self.update_progress)
        self.worker.log_signal.connect(self.log_message)
        self.worker.finished_signal.connect(
            lambda success, msg: self.on_backup_finished(success, msg, str(out_path))
        )
        self.worker.start()

    def on_backup_finished(self, success, message, out_path):
        """백업 완료 콜백"""
        self.enable_buttons(True)
        self.update_progress(0)
        if success:
            self.log_message("===== 백업 완료 =====")
            QMessageBox.information(self, "백업 완료",
                f"백업이 완료되었습니다.\n\n저장 위치:\n{out_path}")
        else:
            self.log_message(f"오류: {message}")
            QMessageBox.critical(self, "백업 실패", f"백업 중 오류가 발생했습니다:\n{message}")
        if self.worker:
            self.worker.deleteLater()
            self.worker = None

    def on_install_finished(self, success, message, install_type="전체"):
        """설치 완료 콜백"""
        # 버튼 재활성화
        self.enable_buttons(True)
        self.update_progress(0)

        if success:
            self.log_message(f"===== {install_type} 설치 완료 =====")
            self.install_completed.emit()
            QMessageBox.information(self, "설치 완료", f"{install_type} 설치가 완료되었습니다.")
        else:
            self.log_message(f"오류: {message}")
            self.install_failed.emit(message)
            QMessageBox.critical(self, "설치 실패", f"설치 중 오류가 발생했습니다:\n{message}")

        # 워커 정리
        if self.worker:
            self.worker.deleteLater()
            self.worker = None