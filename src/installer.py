"""
설치 관리 모듈
Mubig_UI 설치 기능 구현
"""

import os
import stat
import shutil
import zipfile
import tempfile
from pathlib import Path
from typing import List, Callable, Optional

class Installer:
    """설치 관리 클래스"""

    def __init__(self, settings):
        self.settings = settings
        self.temp_backup_dir = None

    @staticmethod
    def _force_rmtree(path):
        """권한 문제를 우회하는 안전한 폴더 삭제 (Windows WinError 145 / macOS 호환)"""
        import sys
        def _handle_error(func, fpath, excinfo):
            try:
                os.chmod(fpath, stat.S_IWRITE)
                func(fpath)
            except Exception:
                pass
        # Python 3.12+ 에서는 onerror 대신 onexc 사용
        if sys.version_info >= (3, 12):
            def _handle_exc(func, fpath, exc):
                _handle_error(func, fpath, None)
            shutil.rmtree(path, onexc=_handle_exc)
        else:
            shutil.rmtree(path, onerror=_handle_error)

    def full_install(self, zip_path: str,
                    progress_callback: Callable = None,
                    log_callback: Callable = None) -> bool:
        try:
            version = self.settings.get_selected_version()
            game_path = Path(self.settings.get_game_path(version))

            if not game_path.exists():
                self._log("게임 경로를 찾을 수 없습니다.", log_callback)
                return False

            version_path = game_path
            self._log(f"게임 경로: {version_path}", log_callback)
            self._update_progress(10, progress_callback)

            self._log("백업 파일 저장 중...", log_callback)
            backed_up_files = self._backup_files(version_path, version, log_callback)
            self._update_progress(20, progress_callback)

            self._log("기존 폴더 삭제 중...", log_callback)
            for folder in ["Fonts", "Interface", "WTF"]:
                folder_path = version_path / folder
                if folder_path.exists():
                    try:
                        self._force_rmtree(folder_path)
                        self._log(f"{folder} 폴더 삭제됨", log_callback)
                    except Exception as e:
                        self._log(f"  {folder} 폴더 삭제 실패: {e}", log_callback)
            self._update_progress(30, progress_callback)

            self._log("압축 파일 해제 중...", log_callback)
            with tempfile.TemporaryDirectory() as temp_dir:
                temp_path = Path(temp_dir)

                with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                    total_files = len(zip_ref.namelist())
                    extracted_count = 0
                    for member in zip_ref.namelist():
                        zip_ref.extract(member, temp_dir)
                        extracted_count += 1
                        if extracted_count % 100 == 0:
                            progress = 30 + int((extracted_count / total_files) * 40)
                            self._update_progress(progress, progress_callback)

                self._update_progress(70, progress_callback)

                self._log("파일 복사 중...", log_callback)
                for folder in ["Fonts", "Interface", "WTF"]:
                    src = temp_path / folder
                    if src.exists():
                        dst = version_path / folder
                        shutil.copytree(src, dst, dirs_exist_ok=True)
                        self._log(f"{folder} 폴더 복사됨", log_callback)
                self._update_progress(80, progress_callback)

                self._apply_account_names_for_version(version_path, version, log_callback)
                self._update_progress(90, progress_callback)

            self._log("백업 파일 복원 중...", log_callback)
            self._restore_backup_files(backed_up_files, version_path, log_callback)
            self._update_progress(100, progress_callback)

            return True

        except Exception as e:
            self._log(f"설치 실패: {str(e)}", log_callback)
            return False

    def install_interface(self, zip_path: str,
                         progress_callback: Callable = None,
                         log_callback: Callable = None) -> bool:
        try:
            version = self.settings.get_selected_version()
            game_path = Path(self.settings.get_game_path(version))

            if not game_path.exists():
                self._log("게임 경로를 찾을 수 없습니다.", log_callback)
                return False

            version_path = game_path
            self._log(f"Interface 설치 시작: {version_path}", log_callback)
            self._update_progress(20, progress_callback)

            with tempfile.TemporaryDirectory() as temp_dir:
                temp_path = Path(temp_dir)

                self._log("압축 파일에서 Interface 폴더 추출 중...", log_callback)
                with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                    interface_files = [f for f in zip_ref.namelist() if f.startswith("Interface/")]
                    total_files = len(interface_files)
                    extracted_count = 0
                    for file in interface_files:
                        zip_ref.extract(file, temp_dir)
                        extracted_count += 1
                        if extracted_count % 50 == 0:
                            progress = 20 + int((extracted_count / total_files) * 50)
                            self._update_progress(progress, progress_callback)

                self._update_progress(70, progress_callback)

                src = temp_path / "Interface"
                if src.exists():
                    dst = version_path / "Interface"
                    if dst.exists():
                        try:
                            self._force_rmtree(dst)
                        except Exception as e:
                            self._log(f"Interface 폴더 삭제 실패: {e}", log_callback)
                    shutil.copytree(src, dst, dirs_exist_ok=True)
                    self._log("Interface 폴더 복사 완료", log_callback)

            self._update_progress(100, progress_callback)
            self._log("Interface 설치 완료", log_callback)
            return True

        except Exception as e:
            self._log(f"설치 실패: {str(e)}", log_callback)
            return False

    def install_wtf(self, zip_path: str, selected_files: List[str],
                   progress_callback: Callable = None,
                   log_callback: Callable = None) -> bool:
        try:
            version = self.settings.get_selected_version()
            game_path = Path(self.settings.get_game_path(version))

            if not game_path.exists():
                self._log("게임 경로를 찾을 수 없습니다.", log_callback)
                return False

            effective_accounts = self._get_effective_accounts(version)
            if not effective_accounts:
                self._log("계정명이 설정되지 않았습니다.", log_callback)
                return False

            version_path = game_path
            self._log(f"WTF 설치 시작: {version_path}", log_callback)
            self._update_progress(20, progress_callback)

            with tempfile.TemporaryDirectory() as temp_dir:
                temp_path = Path(temp_dir)

                with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                    self._log("압축 파일 해제 중...", log_callback)
                    zip_ref.extractall(temp_dir)

                self._update_progress(50, progress_callback)

                self._log("선택된 파일 복사 중...", log_callback)
                saved_vars_src = temp_path / "WTF" / "Account" / "계정명" / "SavedVariables"

                for acct in effective_accounts:
                    self._log(f"  계정: {acct}", log_callback)
                    saved_vars_dst = version_path / "WTF" / "Account" / acct / "SavedVariables"
                    saved_vars_dst.mkdir(parents=True, exist_ok=True)

                    copied_count = 0
                    for file_name in selected_files:
                        for ext in ['', '.bak']:
                            src_file = saved_vars_src / f"{file_name}{ext}"
                            if src_file.exists():
                                dst_file = saved_vars_dst / f"{file_name}{ext}"
                                shutil.copy2(src_file, dst_file)
                                self._log(f"    {file_name}{ext}", log_callback)
                        copied_count += 1
                        progress = 50 + int((copied_count / len(selected_files)) * 40)
                        self._update_progress(progress, progress_callback)

            self._update_progress(100, progress_callback)
            self._log("WTF 설치 완료", log_callback)
            return True

        except Exception as e:
            self._log(f"설치 실패: {str(e)}", log_callback)
            return False

    def _get_effective_accounts(self, version: str) -> List[str]:
        """
        버전에 따라 실제 적용할 계정명 목록 반환.
        포에버 버전:
          - '#' 포함(타입 B) → 그대로 사용
          - '#' 미포함(타입 A) → forever 계정명 사용 (없으면 main 사용)
        포에버 외:
          - 항상 main 계정명 사용
        """
        forever_map = self.settings.get_account_forever_map()

        if not forever_map:
            # 구버전 호환
            names = self.settings.get_account_names()
            if not names:
                n = self.settings.get_account_name()
                if n:
                    names = [n]
            return names

        result = []
        for entry in forever_map:
            main_name = entry.get('main', '')
            forever_name = entry.get('forever')

            if version == 'forever':
                if '#' in main_name:
                    result.append(main_name)
                else:
                    result.append(forever_name if forever_name else main_name)
            else:
                result.append(main_name)

        return [r for r in result if r]

    def _apply_account_names_for_version(self, version_path: Path, version: str, log_callback: Callable):
        effective_accounts = self._get_effective_accounts(version)
        if effective_accounts:
            self._log(f"계정명 처리 시작 ({len(effective_accounts)}개)", log_callback)
            self._apply_account_names(version_path, effective_accounts, log_callback)

    def _apply_account_names(self, version_path: Path, account_names: list, log_callback: Callable):
        account_folder = version_path / "WTF" / "Account"
        if not account_folder.exists():
            self._log("  WTF/Account 폴더 없음, 건너뜀", log_callback)
            return

        source_folder = None
        for folder in account_folder.iterdir():
            if folder.is_dir() and folder.name == "계정명":
                source_folder = folder
                break

        if source_folder is None:
            self._log("  '계정명' 폴더를 찾을 수 없음, 건너뜀", log_callback)
            return

        for idx, acct in enumerate(account_names):
            target = account_folder / acct
            if idx == 0:
                if target.exists():
                    self._force_rmtree(target)
                source_folder.rename(target)
                self._log(f"  계정 폴더 이름 변경: 계정명 → {acct}", log_callback)
                source_folder = target
            else:
                if target.exists():
                    self._force_rmtree(target)
                shutil.copytree(source_folder, target)
                self._log(f"  계정 폴더 복사 생성: {acct}", log_callback)

    def _backup_files(self, game_path: Path, version: str, log_callback: Callable) -> dict:
        backed_up = {}

        try:
            self.temp_backup_dir = tempfile.mkdtemp(prefix="mubig_backup_")
            temp_backup_path = Path(self.temp_backup_dir)

            # 자동 백업 1: WTF/Config.wtf
            config_wtf = game_path / "WTF" / "Config.wtf"
            if config_wtf.exists():
                dst = temp_backup_path / "auto" / "WTF" / "Config.wtf"
                dst.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(config_wtf, dst)
                backed_up["__auto__WTF/Config.wtf"] = dst
                self._log("  [자동백업] WTF/Config.wtf", log_callback)

            # 자동 백업 2: WTF/Account/<계정명>/ 일반 파일
            effective_accounts = self._get_effective_accounts(version)
            for acct in effective_accounts:
                acct_folder = game_path / "WTF" / "Account" / acct
                if not acct_folder.exists():
                    continue
                for item in acct_folder.iterdir():
                    if item.is_file() and item.suffix.lower() not in ('.zip', '.7z', '.rar'):
                        rel = f"WTF/Account/{acct}/{item.name}"
                        key = f"__auto__{rel}"
                        dst = temp_backup_path / "auto" / rel
                        dst.parent.mkdir(parents=True, exist_ok=True)
                        shutil.copy2(item, dst)
                        backed_up[key] = dst
                        self._log(f"  [자동백업] {rel}", log_callback)

            # 사용자 지정 백업: 폴더
            for folder in self.settings.get_version_backup_folders(version):
                src = game_path / folder
                if src.exists() and src.is_dir():
                    dst = temp_backup_path / "folders" / folder
                    dst.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copytree(src, dst, dirs_exist_ok=True)
                    backed_up[folder] = dst
                    self._log(f"  백업: {folder}", log_callback)

            # 사용자 지정 백업: 파일
            account_name = self.settings.get_account_name()
            backup_files = self.settings.get_version_backup_files(version)
            if backup_files:
                self._log(f"  설정 파일 백업 시도... (계정명: {account_name})", log_callback)

            for file in backup_files:
                if account_name:
                    file = file.replace("계정명", account_name)
                for ext in ['', '.bak']:
                    src_file = game_path / (file + ext)
                    if src_file.exists() and src_file.is_file():
                        dst_file = temp_backup_path / "files" / (file + ext)
                        dst_file.parent.mkdir(parents=True, exist_ok=True)
                        shutil.copy2(src_file, dst_file)
                        backed_up[file + ext] = dst_file
                        self._log(f"  백업 완료: {file + ext}", log_callback)
                    else:
                        if ext == '':
                            self._log(f"  백업 파일 없음: ({src_file})", log_callback)

        except Exception as e:
            self._log(f"백업 중 오류: {str(e)}", log_callback)

        return backed_up

    def _restore_backup_files(self, backed_up: dict, game_path: Path, log_callback: Callable):
        try:
            for key, backup_path in backed_up.items():
                if key.startswith("__auto__"):
                    rel = key[len("__auto__"):]
                    dst = game_path / Path(rel)
                else:
                    dst = game_path / key

                dst.parent.mkdir(parents=True, exist_ok=True)

                if backup_path.is_dir():
                    shutil.copytree(backup_path, dst, dirs_exist_ok=True)
                else:
                    shutil.copy2(backup_path, dst)

                self._log(f"  복원: {key.replace('__auto__', '')}", log_callback)

            if self.temp_backup_dir and Path(self.temp_backup_dir).exists():
                shutil.rmtree(self.temp_backup_dir, ignore_errors=True)

        except Exception as e:
            self._log(f"복원 중 오류: {str(e)}", log_callback)

    def _log(self, message: str, callback: Callable):
        if callback:
            callback(message)

    def _update_progress(self, value: int, callback: Callable):
        if callback:
            callback(value)
