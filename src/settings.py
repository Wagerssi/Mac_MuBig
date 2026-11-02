"""
설정 관리 모듈
프로그램 설정을 관리하고 저장/불러오기 기능 제공
"""

import json
import os
import platform
from pathlib import Path
from typing import Dict, List, Any


class Settings:
    """프로그램 설정 관리 클래스"""

    CONFIG_VERSION = '2.4'

    DEFAULT_CONFIG = {
        'config_version': CONFIG_VERSION,
        'auth': {
            'is_authenticated': False,
            'auth_url': '',
            'cached_auth': None,
        },
        'game_versions': {
            'retail':      {'name': '한밤',       'path': ''},
            'classic':     {'name': '판다리아',   'path': ''},
            'anniversary': {'name': '불타는성전', 'path': ''},
            'classic_era': {'name': '클래식',     'path': ''},
            'forever':     {'name': '포에버',     'path': ''},
        },
        'selected_version': 'retail',
        'account_name': '',
        'account_names': [],
        # forever 전용 계정 목록: [{"main": "일반계정명", "forever": "포에버계정명"}, ...]
        # main 계정이 '#' 포함이면 forever 키 없음 (일반 계정으로 포에버도 적용)
        # main 계정이 '#' 미포함이면 forever 키에 포에버 전용 계정명 저장
        'account_forever_map': [],
        'backup_save_folder': '',
        'backup_items': {
            'retail':      {'folders': [], 'files': []},
            'classic':     {'folders': [], 'files': []},
            'anniversary': {'folders': [], 'files': []},
            'classic_era': {'folders': [], 'files': []},
            'forever':     {'folders': [], 'files': []},
        },
    }

    def __init__(self):
        # OS별 설정 파일 저장 위치
        if platform.system() == 'Darwin':
            config_dir = Path.home() / 'Library' / 'Application Support' / 'MuBig_UI'
            config_dir.mkdir(parents=True, exist_ok=True)
            self.config_path = config_dir / 'MuBig_config.json'
        else:
            self.config_path = Path('MuBig_config.json')
        is_first_run = not self.config_path.exists()
        if is_first_run:
            self.config = self._deep_copy(self.DEFAULT_CONFIG)
            self.save_config()
        else:
            self.load_config()

    def _deep_copy(self, d):
        import copy
        return copy.deepcopy(d)

    def load_config(self):
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                loaded = json.load(f)
            self.config = self._merge_configs(self._deep_copy(self.DEFAULT_CONFIG), loaded)
            migrated = self._migrate(self.config)
            if migrated:
                print('설정 파일 마이그레이션 완료, 저장 중...')
                self.save_config()
        except Exception as e:
            print(f'설정 파일 로드 오류: {e}')
            self.config = self._deep_copy(self.DEFAULT_CONFIG)

    def _migrate(self, config: dict) -> bool:
        """
        구버전 설정을 현재 버전으로 마이그레이션합니다.
        변경이 발생하면 True 반환 (저장 필요).
        """
        changed = False
        old_ver = config.get('config_version', '0.0')

        # ── v2.3 이하 → v2.4 마이그레이션 ───────────────────────────────
        # 1) game_versions 에 forever 항목이 없으면 추가
        gv = config.setdefault('game_versions', {})
        if 'forever' not in gv:
            gv['forever'] = {'name': '포에버', 'path': ''}
            changed = True
            print('  [migrate] game_versions.forever 추가')

        # 2) backup_items 에 forever 항목이 없으면 추가
        bi = config.setdefault('backup_items', {})
        if 'forever' not in bi:
            bi['forever'] = {'folders': [], 'files': []}
            changed = True
            print('  [migrate] backup_items.forever 추가')

        # 3) account_forever_map 없으면 account_names 기반으로 자동 생성
        #    - '#' 포함 계정 → forever: None (타입 B, 포에버도 main으로)
        #    - '#' 미포함 계정 → forever: None (타입 A, 포에버 계정은 미등록 상태)
        if 'account_forever_map' not in config:
            names = config.get('account_names', [])
            if not names:
                single = config.get('account_name', '')
                names = [single] if single else []
            config['account_forever_map'] = [
                {'main': n, 'forever': None} for n in names
            ]
            changed = True
            print(f'  [migrate] account_forever_map 생성 ({len(names)}개 계정)')

        # 4) 버전 스탬프 업데이트
        if old_ver != self.CONFIG_VERSION:
            config['config_version'] = self.CONFIG_VERSION
            changed = True
            print(f'  [migrate] config_version {old_ver} → {self.CONFIG_VERSION}')

        return changed

    def _merge_configs(self, default, loaded):
        merged = default.copy()
        for key, value in loaded.items():
            if key in merged and isinstance(merged[key], dict) and isinstance(value, dict):
                merged[key] = self._merge_configs(merged[key], value)
            elif key == 'backup_files' and isinstance(value, list) and len(value) == 0:
                pass
            else:
                merged[key] = value
        return merged

    def save_config(self):
        try:
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f'설정 파일 저장 오류: {e}')

    def _remove_hidden_attribute(self):
        if platform.system() != 'Windows' or not self.config_path.exists():
            return
        try:
            import ctypes
            path_str = str(self.config_path.absolute())
            attrs = ctypes.windll.kernel32.GetFileAttributesW(path_str)
            if attrs != -1:
                ctypes.windll.kernel32.SetFileAttributesW(path_str, attrs & ~2)
        except Exception:
            pass

    def get(self, *keys, default=None):
        value = self.config
        for key in keys:
            if isinstance(value, dict):
                value = value.get(key, default)
            else:
                return default
        return value

    def set(self, *keys, value):
        config = self.config
        for key in keys[:-1]:
            if key not in config:
                config[key] = {}
            config = config[key]
        config[keys[-1]] = value
        self.save_config()

    # 인증
    def is_authenticated(self) -> bool:
        return self.get('auth', 'is_authenticated', default=False)

    def set_authenticated(self, status: bool, auth_url: str = ''):
        self.set('auth', 'is_authenticated', value=status)
        if auth_url:
            self.set('auth', 'auth_url', value=auth_url)
        self.save_config()

    # 게임 버전 경로
    def get_game_path(self, version: str) -> str:
        return self.get('game_versions', version, 'path', default='')

    def set_game_path(self, version: str, path: str):
        self.set('game_versions', version, 'path', value=path)

    def get_game_version_name(self, version: str) -> str:
        defaults = {'retail': '한밤', 'classic': '판다리아',
                    'anniversary': '불타는성전', 'classic_era': '클래식', 'forever': '포에버'}
        return self.get('game_versions', version, 'name', default=defaults.get(version, version))

    def set_game_version_name(self, version: str, name: str):
        self.set('game_versions', version, 'name', value=name)

    def get_selected_version(self) -> str:
        return self.get('selected_version', default='retail')

    def set_selected_version(self, version: str):
        self.set('selected_version', value=version)

    # 백업 저장 폴더
    def get_backup_save_folder(self) -> str:
        return self.get('backup_save_folder', default='')

    def set_backup_save_folder(self, path: str):
        self.set('backup_save_folder', value=path)

    # 계정명 (단일 – 하위호환)
    def get_account_name(self) -> str:
        return self.get('account_name', default='')

    def set_account_name(self, name: str):
        self.set('account_name', value=name)

    # 계정명 목록 (다중)
    def get_account_names(self) -> List[str]:
        return self.get('account_names', default=[])

    def set_account_names(self, names: List[str]):
        self.set('account_names', value=names)

    def add_account_name(self, name: str):
        names = self.get_account_names()
        if name and name not in names:
            names.append(name)
            self.set_account_names(names)

    def remove_account_name(self, name: str):
        names = self.get_account_names()
        if name in names:
            names.remove(name)
            self.set_account_names(names)

    # 포에버 계정 맵: [{"main": "계정명", "forever": "포에버계정명"}, ...]
    def get_account_forever_map(self) -> List[dict]:
        return self.get('account_forever_map', default=[])

    def set_account_forever_map(self, mapping: List[dict]):
        self.set('account_forever_map', value=mapping)

    def get_forever_account_for(self, main_name: str) -> str:
        """main_name 에 대응하는 포에버 전용 계정명 반환 (없으면 main_name 반환)"""
        for entry in self.get_account_forever_map():
            if entry.get('main') == main_name:
                return entry.get('forever', main_name)
        return main_name

    # 백업 목록
    def get_backup_folders(self):
        return self.get('backup_folders', default=[])

    def set_backup_folders(self, folders):
        self.set('backup_folders', value=folders)

    def get_backup_files(self):
        files = self.get('backup_files', default=[])
        account = self.get_account_name()
        return [f.replace('계정명', account) for f in files]

    def set_backup_files(self, files):
        self.set('backup_files', value=files)

    def get_version_backup_folders(self, version: str) -> List[str]:
        return self.get('backup_items', version, 'folders', default=[])

    def set_version_backup_folders(self, version: str, folders: List[str]):
        self.set('backup_items', version, 'folders', value=folders)

    def get_version_backup_files(self, version: str) -> List[str]:
        return self.get('backup_items', version, 'files', default=[])

    def set_version_backup_files(self, version: str, files: List[str]):
        self.set('backup_items', version, 'files', value=files)

    def get_default_backup_folders(self, version: str) -> List[str]:
        return self.DEFAULT_CONFIG.get('backup_items', {}).get(version, {}).get('folders', [])

    def get_default_backup_files(self, version: str) -> List[str]:
        return self.DEFAULT_CONFIG.get('backup_items', {}).get(version, {}).get('files', [])
