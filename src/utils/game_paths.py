"""
게임 경로 관리 유틸리티
WoW 게임 경로 관련 유틸리티 함수 (Windows / macOS 공통)
"""

import os
import platform
from pathlib import Path
from typing import Optional, Dict

# 지원하는 게임 버전 정의
GAME_VERSIONS = {
    'retail':      {'folder': '_Retail_',      'name': '한밤'},
    'classic':     {'folder': '_Classic_',     'name': '판다리아'},
    'anniversary': {'folder': '_anniversary_', 'name': '불타는성전'},
    'classic_era': {'folder': '_Classic_Era_', 'name': '클래식'},
    'forever':     {'folder': '_forever_',     'name': '포에버'},
}

VERSION_ORDER = ['retail', 'classic', 'anniversary', 'classic_era', 'forever']


def _get_common_wow_roots() -> list:
    """OS별 WoW 기본 설치 경로 목록"""
    if platform.system() == 'Darwin':  # macOS
        return [
            '/Applications/World of Warcraft',
            os.path.expanduser('~/Applications/World of Warcraft'),
        ]
    else:  # Windows
        return [
            'C:\\Program Files (x86)\\World of Warcraft',
            'C:\\Program Files\\World of Warcraft',
            'D:\\Games\\World of Warcraft',
            'D:\\World of Warcraft',
            'E:\\Games\\World of Warcraft',
            'E:\\World of Warcraft',
        ]


def find_wow_root() -> Optional[str]:
    """WoW 설치 루트 폴더를 찾습니다"""

    # Windows: 레지스트리 탐색
    if platform.system() == 'Windows':
        try:
            import winreg
            reg_paths = [
                'SOFTWARE\\WOW6432Node\\Blizzard Entertainment\\World of Warcraft',
                'SOFTWARE\\Blizzard Entertainment\\World of Warcraft',
            ]
            for reg_path in reg_paths:
                try:
                    key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, reg_path)
                    install_path, _ = winreg.QueryValueEx(key, 'InstallPath')
                    if install_path and os.path.exists(install_path):
                        p = Path(install_path)
                        for ver_info in GAME_VERSIONS.values():
                            if p.name.lower() == ver_info['folder'].lower():
                                p = p.parent
                                break
                        if p.exists():
                            return str(p)
                except Exception:
                    pass
        except Exception:
            pass

    # 공통 경로 탐색 (Windows 폴백 + macOS)
    for root in _get_common_wow_roots():
        if os.path.exists(root):
            for ver_info in GAME_VERSIONS.values():
                if os.path.exists(os.path.join(root, ver_info['folder'])):
                    return root

    return None


def find_wow_installation_paths() -> Dict[str, str]:
    """설치된 게임 버전별 경로를 반환합니다"""
    result: Dict[str, str] = {}
    wow_root = find_wow_root()
    if not wow_root:
        print('레지스트리/공통 경로에서 WoW 루트를 찾지 못했습니다.')
        return result

    for key, ver_info in GAME_VERSIONS.items():
        ver_path = os.path.join(wow_root, ver_info['folder'])
        if os.path.exists(ver_path):
            result[key] = ver_path
            print(f'[게임경로 자동감지] {key}: {ver_path}')

    return result


def get_wow_version_from_path(game_path: str) -> Optional[str]:
    if not os.path.exists(game_path):
        return None
    path_lower = game_path.lower()
    for key, ver_info in GAME_VERSIONS.items():
        if ver_info['folder'].lower() in path_lower:
            return key
    return None


def get_account_folders(game_path: str):
    account_path = Path(game_path) / 'WTF' / 'Account'
    accounts = []
    if account_path.exists():
        for item in account_path.iterdir():
            if item.is_dir() and not item.name.startswith('.') and item.name not in ('SavedVariables',):
                accounts.append(item.name)
    return sorted(accounts)


def validate_game_installation(game_path: str) -> dict:
    result = {'valid': False, 'has_executable': False,
               'has_interface': False, 'has_wtf': False, 'version': None}
    if not os.path.exists(game_path):
        return result
    path_obj = Path(game_path)

    # Windows: .exe / macOS: .app 번들
    executables_win = ('Wow.exe', 'WowClassic.exe', 'WowClassicEra.exe')
    executables_mac = ('World of Warcraft.app', 'WoW Classic.app', 'WoW Classic Era.app')
    exes = executables_mac if platform.system() == 'Darwin' else executables_win
    for exe in exes:
        if (path_obj / exe).exists():
            result['has_executable'] = True
            break

    result['has_interface'] = (path_obj / 'Interface').exists()
    result['has_wtf'] = (path_obj / 'WTF').exists()
    result['version'] = get_wow_version_from_path(game_path)
    result['valid'] = result['has_executable'] or result['has_interface'] or result['has_wtf']
    return result


def create_default_folders(game_path: str) -> bool:
    path_obj = Path(game_path)
    try:
        for folder in ('Interface/AddOns', 'WTF/Account', 'Fonts'):
            (path_obj / folder).mkdir(parents=True, exist_ok=True)
        return True
    except Exception as e:
        print(f'폴더 생성 실패: {str(e)}')
        return False
