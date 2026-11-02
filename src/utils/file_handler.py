"""
파일 처리 유틸리티
파일 및 디렉토리 관련 유틸리티 함수
"""

import os
import shutil
import zipfile
from pathlib import Path
from typing import List, Optional

def is_valid_wow_path(path: str) -> bool:
    """WoW 게임 경로 유효성 확인"""
    if not path or not os.path.exists(path):
        return False

    path_obj = Path(path)
    # WoW 실행 파일 체크
    wow_executables = ["Wow.exe", "WowClassic.exe", "WowClassicEra.exe"]

    for exe in wow_executables:
        if (path_obj / exe).exists():
            return True

    return False

def get_addon_folders(game_path: str) -> List[str]:
    """AddOns 폴더 목록 가져오기"""
    addons_path = Path(game_path) / "Interface" / "AddOns"

    if not addons_path.exists():
        return []

    folders = []
    for item in addons_path.iterdir():
        if item.is_dir() and not item.name.startswith('.'):
            folders.append(item.name)

    return sorted(folders)

def get_saved_variables_files(game_path: str, account_name: str) -> List[str]:
    """SavedVariables 파일 목록 가져오기"""
    sv_path = Path(game_path) / "WTF" / "Account" / account_name / "SavedVariables"

    if not sv_path.exists():
        return []

    files = []
    for item in sv_path.iterdir():
        if item.is_file() and item.suffix == ".lua":
            # .lua.bak 파일은 제외
            if not item.name.endswith(".lua.bak"):
                files.append(item.name)

    return sorted(files)

def safe_delete_directory(path: str) -> bool:
    """디렉토리 안전하게 삭제"""
    try:
        if os.path.exists(path):
            shutil.rmtree(path, ignore_errors=True)
        return True
    except Exception as e:
        print(f"디렉토리 삭제 실패: {str(e)}")
        return False

def safe_copy_file(src: str, dst: str) -> bool:
    """파일 안전하게 복사"""
    try:
        src_path = Path(src)
        dst_path = Path(dst)

        # 대상 디렉토리 생성
        dst_path.parent.mkdir(parents=True, exist_ok=True)

        # 파일 복사
        shutil.copy2(src_path, dst_path)
        return True
    except Exception as e:
        print(f"파일 복사 실패: {str(e)}")
        return False

def safe_copy_directory(src: str, dst: str) -> bool:
    """디렉토리 안전하게 복사"""
    try:
        src_path = Path(src)
        dst_path = Path(dst)

        # 대상 디렉토리가 있으면 삭제
        if dst_path.exists():
            shutil.rmtree(dst_path, ignore_errors=True)

        # 디렉토리 복사
        shutil.copytree(src_path, dst_path)
        return True
    except Exception as e:
        print(f"디렉토리 복사 실패: {str(e)}")
        return False

def extract_zip_file(zip_path: str, extract_to: str,
                    specific_folder: Optional[str] = None) -> bool:
    """ZIP 파일 압축 해제"""
    try:
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            if specific_folder:
                # 특정 폴더만 압축 해제
                members = [m for m in zip_ref.namelist()
                          if m.startswith(specific_folder + '/')]
                for member in members:
                    zip_ref.extract(member, extract_to)
            else:
                # 전체 압축 해제
                zip_ref.extractall(extract_to)
        return True
    except Exception as e:
        print(f"압축 해제 실패: {str(e)}")
        return False

def get_zip_contents(zip_path: str, folder: Optional[str] = None) -> List[str]:
    """ZIP 파일 내용 목록 가져오기"""
    contents = []
    try:
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            if folder:
                contents = [f for f in zip_ref.namelist()
                           if f.startswith(folder + '/')]
            else:
                contents = zip_ref.namelist()
    except Exception as e:
        print(f"ZIP 파일 읽기 실패: {str(e)}")

    return contents

def create_backup(files: List[str], backup_dir: str) -> bool:
    """파일 백업 생성"""
    try:
        backup_path = Path(backup_dir)
        backup_path.mkdir(parents=True, exist_ok=True)

        for file_path in files:
            if os.path.exists(file_path):
                file_obj = Path(file_path)
                # 상대 경로 유지하면서 백업
                relative_path = file_obj.relative_to(file_obj.anchor)
                dst = backup_path / relative_path
                dst.parent.mkdir(parents=True, exist_ok=True)

                if file_obj.is_dir():
                    shutil.copytree(file_path, dst)
                else:
                    shutil.copy2(file_path, dst)

        return True
    except Exception as e:
        print(f"백업 생성 실패: {str(e)}")
        return False

def restore_backup(backup_dir: str, restore_to: str) -> bool:
    """백업 복원"""
    try:
        backup_path = Path(backup_dir)
        restore_path = Path(restore_to)

        if not backup_path.exists():
            return False

        # 백업 파일들 복원
        for item in backup_path.rglob('*'):
            if item.is_file():
                # 상대 경로 계산
                relative_path = item.relative_to(backup_path)
                dst = restore_path / relative_path
                dst.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(item, dst)

        return True
    except Exception as e:
        print(f"백업 복원 실패: {str(e)}")
        return False