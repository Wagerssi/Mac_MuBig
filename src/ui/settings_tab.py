"""
설정 탭
프로그램 설정 관리 UI
"""

import os
from pathlib import Path

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QPushButton, QLabel, QLineEdit, QGroupBox,
    QListWidget, QListWidgetItem, QFileDialog, QMessageBox,
    QAbstractItemView, QComboBox, QSizePolicy, QDialog,
    QDialogButtonBox,
)
from PySide6.QtCore import Qt
from .custom_widgets import OutlinedButton
from ..utils.game_paths import find_wow_installation_paths, GAME_VERSIONS, VERSION_ORDER


class SettingsTab(QWidget):
    """설정 탭 위젯"""

    def __init__(self, settings):
        super().__init__()
        self.settings = settings
        self.setup_ui()
        self.load_settings()

    def setup_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(10)
        self.create_path_section(layout)
        self.create_account_section(layout)
        self.create_backup_section(layout)
        layout.addStretch()
        self.setLayout(layout)

    def create_path_section(self, parent_layout):
        group = QGroupBox('Mubig_UI 설치 경로 설정')
        layout = QVBoxLayout()
        layout.setSpacing(6)

        row = QHBoxLayout()
        row.setSpacing(8)

        self.version_combo = QComboBox()
        self.version_combo.setFixedWidth(130)
        for key in VERSION_ORDER:
            display = GAME_VERSIONS[key]['name']
            self.version_combo.addItem(display, key)
        self.version_combo.currentIndexChanged.connect(self._on_version_combo_changed)

        self.game_path_label = QLabel('미설정')
        self.game_path_label.setStyleSheet('color: #aaa;')
        self.game_path_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self.game_path_label.setWordWrap(True)

        browse_btn = OutlinedButton('찾아보기')
        browse_btn.setFixedWidth(80)
        browse_btn.clicked.connect(self._browse_game_path)

        row.addWidget(self.version_combo)
        row.addWidget(self.game_path_label, 1)
        row.addWidget(browse_btn)
        layout.addLayout(row)

        # 자동 탐색 + 백업 폴더 설정 버튼
        btn_row2 = QHBoxLayout()
        btn_row2.setSpacing(6)
        auto_btn = OutlinedButton('게임 경로 자동 설정')
        auto_btn.clicked.connect(self._auto_detect_paths)
        btn_row2.addWidget(auto_btn)
        backup_folder_btn = OutlinedButton('백업 폴더 설정')
        backup_folder_btn.clicked.connect(self._set_backup_folder)
        btn_row2.addWidget(backup_folder_btn)
        layout.addLayout(btn_row2)

        self.backup_folder_label = QLabel()
        self._refresh_backup_folder_label()
        self.backup_folder_label.setStyleSheet('color: #888; font-size: 11px;')
        self.backup_folder_label.setWordWrap(True)
        layout.addWidget(self.backup_folder_label)

        group.setLayout(layout)
        parent_layout.addWidget(group)

    def _on_version_combo_changed(self, index):
        key = self.version_combo.currentData()
        path = self.settings.get_game_path(key)
        self._update_path_label(path)

    def _update_path_label(self, path):
        if path:
            self.game_path_label.setText(path)
            self.game_path_label.setStyleSheet('color: #eee;')
        else:
            self.game_path_label.setText('미설정')
            self.game_path_label.setStyleSheet('color: #aaa;')

    def _browse_game_path(self):
        key = self.version_combo.currentData()
        current = self.settings.get_game_path(key)
        folder = QFileDialog.getExistingDirectory(
            self, f'{GAME_VERSIONS[key]["name"]} 게임 경로 선택',
            current if current else ''
        )
        if folder:
            self.settings.set_game_path(key, folder)
            self._update_path_label(folder)
            self._autosave()

    def _auto_detect_paths(self):
        found = find_wow_installation_paths()
        if not found:
            QMessageBox.warning(self, '자동 탐색 실패',
                'WoW 설치 경로를 자동으로 찾지 못했습니다.\n찾아보기로 직접 지정해 주세요.')
            return
        for key, path in found.items():
            self.settings.set_game_path(key, path)
        self._on_version_combo_changed(self.version_combo.currentIndex())
        self._autosave()
        lines = [f'{GAME_VERSIONS[k]["name"]}: {p}' for k, p in found.items()]
        QMessageBox.information(self, '자동 탐색 완료',
            '다음 경로가 설정되었습니다:\n\n' + '\n'.join(lines))

    def _refresh_backup_folder_label(self):
        path = self.settings.get_backup_save_folder()
        if path:
            self.backup_folder_label.setText(f'백업 저장 위치: {path}')
        else:
            self.backup_folder_label.setText('백업 저장 위치: 미설정 (WoW 루트 폴더에 저장)')

    def _set_backup_folder(self):
        current = self.settings.get_backup_save_folder()
        folder = QFileDialog.getExistingDirectory(
            self, '백업 파일 저장 폴더 선택',
            current if current else ''
        )
        if folder:
            self.settings.set_backup_save_folder(folder)
            self._refresh_backup_folder_label()
            self._autosave()

    def create_account_section(self, parent_layout):
        group = QGroupBox('계정명 설정')
        layout = QVBoxLayout()
        layout.setSpacing(6)

        input_row = QHBoxLayout()
        input_row.setSpacing(6)
        input_row.addWidget(QLabel('계정명:'))

        self.account_name_edit = QLineEdit()
        self.account_name_edit.setMaxLength(50)
        self.account_name_edit.setFixedWidth(220)
        self.account_name_edit.setPlaceholderText('WoW 계정명 입력')
        self.account_name_edit.returnPressed.connect(self._add_account)
        input_row.addWidget(self.account_name_edit)

        add_btn = OutlinedButton('등록')
        add_btn.setFixedWidth(70)
        add_btn.clicked.connect(self._add_account)
        input_row.addWidget(add_btn)
        input_row.addStretch()
        layout.addLayout(input_row)

        self.account_tag_container = QWidget()
        self.account_tag_container.setStyleSheet('QWidget { background: transparent; }')
        self.account_grid = QGridLayout(self.account_tag_container)
        self.account_grid.setSpacing(6)
        self.account_grid.setContentsMargins(0, 4, 0, 4)
        layout.addWidget(self.account_tag_container)

        # _account_names: list of dict {"main": str, "forever": str or None}
        # forever=None → '#' 포함 계정(배틀넷) → 포에버 포함 모든 버전 적용
        # forever=str  → '#' 미포함 계정(구형) → 포에버에는 forever 값으로 적용
        self._account_names = []

        group.setLayout(layout)
        parent_layout.addWidget(group)

    def _rebuild_account_tags(self):
        while self.account_grid.count():
            item = self.account_grid.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        COLS = 4
        tag_idx = 0
        for entry in self._account_names:
            main_name = entry['main']
            forever_name = entry.get('forever')

            row = tag_idx // COLS
            col = tag_idx % COLS
            self._make_account_tag(main_name, is_forever_only=False,
                                   grid_row=row, grid_col=col)
            tag_idx += 1

            if forever_name:
                row = tag_idx // COLS
                col = tag_idx % COLS
                display = f'{forever_name} (포에버 전용)'
                self._make_account_tag(display, is_forever_only=True,
                                       grid_row=row, grid_col=col,
                                       remove_key=main_name, is_forever_sub=True)
                tag_idx += 1

    def _make_account_tag(self, display_name: str, is_forever_only: bool,
                          grid_row: int, grid_col: int,
                          remove_key: str = None, is_forever_sub: bool = False):
        tag_frame = QWidget()
        if is_forever_only:
            tag_frame.setStyleSheet("""
                QWidget {
                    background-color: #3a2a3a;
                    border: 1px solid #884488;
                    border-radius: 6px;
                }
            """)
        else:
            tag_frame.setStyleSheet("""
                QWidget {
                    background-color: #3a3a3a;
                    border: 1px solid #555;
                    border-radius: 6px;
                }
            """)
        tag_layout = QHBoxLayout(tag_frame)
        tag_layout.setContentsMargins(8, 4, 4, 4)
        tag_layout.setSpacing(4)

        name_label = QLabel(display_name)
        if is_forever_only:
            name_label.setStyleSheet(
                'QLabel { border: none; background: transparent; color: #dd88ff; font-size: 11px; }')
        else:
            name_label.setStyleSheet(
                'QLabel { border: none; background: transparent; color: #eee; }')
        tag_layout.addWidget(name_label)

        x_btn = QPushButton('✕')
        x_btn.setFixedSize(20, 20)
        x_btn.setStyleSheet("""
            QPushButton {
                background-color: #555;
                color: #ccc;
                border: none;
                border-radius: 10px;
                font-size: 11px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #c0392b;
                color: white;
            }
        """)
        x_btn.setProperty('account_main', remove_key if remove_key else display_name)
        x_btn.setProperty('is_forever_sub', is_forever_sub)
        x_btn.clicked.connect(self._on_x_btn_clicked)
        tag_layout.addWidget(x_btn)

        self.account_grid.addWidget(tag_frame, grid_row, grid_col)

    def _add_account(self):
        name = self.account_name_edit.text().strip()
        if not name:
            return

        existing_mains = [e['main'] for e in self._account_names]
        if name in existing_mains:
            self.account_name_edit.clear()
            return

        if '#' in name:
            # 타입 B: 배틀넷 계정 → 모든 버전 동일 적용
            self._account_names.append({'main': name, 'forever': None})
            self._rebuild_account_tags()
            self.account_name_edit.clear()
            self._autosave()
        else:
            # 타입 A: 구형 계정 → 포에버 전용 계정 입력 팝업
            forever_name = self._ask_forever_account(name)
            if forever_name is None:
                # 팝업에서 '취소' → 전체 등록 취소
                self.account_name_edit.clear()
                return
            self._account_names.append({'main': name, 'forever': forever_name if forever_name else None})
            self._rebuild_account_tags()
            self.account_name_edit.clear()
            self._autosave()

    def _ask_forever_account(self, main_name: str):
        """
        타입 A 계정 등록 시 포에버 전용 계정명 입력 팝업
        Returns:
            str  - 입력된 포에버 계정명 (빈 문자열 가능)
            None - 사용자가 '취소' 클릭
        """
        dialog = QDialog(self)
        dialog.setWindowTitle('포에버 전용 계정 등록')
        dialog.setMinimumWidth(380)

        layout = QVBoxLayout()
        layout.setSpacing(10)

        info_label = QLabel(
            f'<b>{main_name}</b> 계정은 와우 포에버에서\n'
            '사용되는 전용 계정명이 다를 수 있습니다.\n\n'
            '와우 포에버 계정을 확인 후 추가로 등록해 주세요.\n'
            '(등록하지 않으면 포에버에는 위 계정명이 그대로 사용됩니다)'
        )
        info_label.setWordWrap(True)
        info_label.setStyleSheet('color: #ddd; line-height: 1.4;')
        layout.addWidget(info_label)

        forever_edit = QLineEdit()
        forever_edit.setPlaceholderText('포에버 전용 계정명 입력 (선택사항)')
        forever_edit.setMaxLength(50)
        layout.addWidget(forever_edit)

        btn_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        btn_box.button(QDialogButtonBox.Ok).setText('등록')
        btn_box.button(QDialogButtonBox.Cancel).setText('취소')
        btn_box.accepted.connect(dialog.accept)
        btn_box.rejected.connect(dialog.reject)
        layout.addWidget(btn_box)

        dialog.setLayout(layout)

        result = dialog.exec()
        if result == QDialog.Accepted:
            return forever_edit.text().strip()
        else:
            return None

    def _on_x_btn_clicked(self):
        main_key = self.sender().property('account_main')
        is_forever_sub = self.sender().property('is_forever_sub')

        if is_forever_sub:
            reply = QMessageBox.question(
                self, '포에버 계정 삭제',
                f'"{main_key}" 계정의 포에버 전용 계정을 삭제하시겠습니까?',
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            if reply == QMessageBox.Yes:
                for entry in self._account_names:
                    if entry['main'] == main_key:
                        entry['forever'] = None
                        break
                self._rebuild_account_tags()
                self._autosave()
        else:
            reply = QMessageBox.question(
                self, '계정 삭제',
                f'계정명 "{main_key}" 을(를) 삭제하시겠습니까?',
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            if reply == QMessageBox.Yes:
                self._account_names = [e for e in self._account_names if e['main'] != main_key]
                self._rebuild_account_tags()
                self._autosave()

    def _on_account_item_clicked(self, item):
        pass

    def create_backup_section(self, parent_layout):
        group = QGroupBox('백업 파일 설정')
        layout = QVBoxLayout()

        btn_layout = QHBoxLayout()
        add_folder_btn = OutlinedButton('폴더 추가')
        add_folder_btn.clicked.connect(self.add_backup_folder)
        add_file_btn = OutlinedButton('파일 추가')
        add_file_btn.clicked.connect(self.add_backup_file)
        btn_layout.addWidget(add_folder_btn)
        btn_layout.addWidget(add_file_btn)
        btn_layout.addStretch()
        layout.addLayout(btn_layout)

        self.backup_list = QListWidget()
        self.backup_list.setMaximumHeight(200)
        self.backup_list.setSelectionMode(QAbstractItemView.MultiSelection)
        self.backup_list.setStyleSheet("""
            QListWidget { border: 1px solid #ccc; }
            QScrollBar:vertical { border: none; background: #f0f0f0; width: 14px; margin: 0px; }
            QScrollBar::handle:vertical { background: #888; min-height: 20px; }
            QScrollBar::handle:vertical:hover { background: #555; }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0px; }
        """)
        layout.addWidget(self.backup_list)

        self.remove_selected_btn = OutlinedButton('선택 항목 제거')
        self.remove_selected_btn.clicked.connect(self.remove_selected_items)
        layout.addWidget(self.remove_selected_btn)

        group.setLayout(layout)
        parent_layout.addWidget(group)

    def add_backup_folder(self):
        valid_paths = {k: self.settings.get_game_path(k) for k in VERSION_ORDER
                       if self.settings.get_game_path(k) and Path(self.settings.get_game_path(k)).exists()}
        if not valid_paths:
            QMessageBox.warning(self, '경고', '먼저 게임 경로를 하나 이상 설정해 주세요.')
            return
        version = self.settings.get_selected_version()
        gp = valid_paths.get(version, list(valid_paths.values())[0])
        base = Path(gp)
        start = str(base / 'Interface' / 'AddOns') if (base / 'Interface' / 'AddOns').exists() else str(base)
        folder = QFileDialog.getExistingDirectory(self, '백업할 폴더 선택', start)
        if not folder:
            return
        fp = Path(folder)
        for key, p in valid_paths.items():
            try:
                rel = fp.relative_to(Path(p))
                vname = self.settings.get_game_version_name(key)
                s = f'[{vname}][폴더] {str(rel).replace(os.sep, "/")}'
                for i in range(self.backup_list.count()):
                    if self.backup_list.item(i).text() == s:
                        return
                self.backup_list.addItem(s)
                self._autosave()
                return
            except ValueError:
                pass
        QMessageBox.warning(self, '잘못된 경로', '선택한 폴더가 게임 경로의 하위가 아닙니다.')

    def add_backup_file(self):
        version = self.settings.get_selected_version()
        # 경로 존재 여부와 무관하게 설정된 경로 우선 사용 (macOS 호환)
        all_paths = {k: self.settings.get_game_path(k) for k in VERSION_ORDER
                     if self.settings.get_game_path(k)}
        valid_paths = {k: p for k, p in all_paths.items() if Path(p).exists()}
        usable_paths = valid_paths if valid_paths else all_paths
        if not usable_paths:
            QMessageBox.warning(self, '경고', '먼저 게임 경로를 하나 이상 설정해 주세요.')
            return
        gp = usable_paths.get(version, list(usable_paths.values())[0])
        base = Path(gp)
        main_names = [e['main'] for e in self._account_names]
        acct = main_names[0] if main_names else '계정명'
        sv = base / 'WTF' / 'Account' / acct / 'SavedVariables'
        start = str(sv if sv.exists() else base)
        files, _ = QFileDialog.getOpenFileNames(
            self, '백업할 파일 선택', start,
            'Lua Files (*.lua);;Text Files (*.txt);;WTF Files (*.wtf);;All Files (*.*)'
        )
        for file in files:
            fp = Path(file).resolve()
            matched = False
            for key, p in usable_paths.items():
                try:
                    rel = fp.relative_to(Path(p).resolve())
                    vname = self.settings.get_game_version_name(key)
                    s = f'[{vname}][파일] {str(rel).replace(os.sep, "/")}'
                    for i in range(self.backup_list.count()):
                        if self.backup_list.item(i).text() == s:
                            matched = True
                            break
                    if not matched:
                        self.backup_list.addItem(s)
                        self._autosave()
                    matched = True
                    break
                except ValueError:
                    pass
            if not matched:
                # 게임 경로 하위가 아니어도 현재 버전 기준으로 추가 허용
                vname = self.settings.get_game_version_name(version)
                s = f'[{vname}][파일] {fp.name}'
                self.backup_list.addItem(s)
                self._autosave()

    def remove_selected_items(self):
        for item in self.backup_list.selectedItems():
            self.backup_list.takeItem(self.backup_list.row(item))
        self._autosave()

    def _autosave(self):
        try:
            main_names = [e['main'] for e in self._account_names]
            self.settings.set_account_names(main_names)
            self.settings.set_account_name(main_names[0] if main_names else '')
            self.settings.set_account_forever_map(list(self._account_names))

            version_folders = {k: [] for k in VERSION_ORDER}
            version_files   = {k: [] for k in VERSION_ORDER}
            for i in range(self.backup_list.count()):
                text = self.backup_list.item(i).text()
                for key in VERSION_ORDER:
                    vname = self.settings.get_game_version_name(key)
                    if text.startswith(f'[{vname}]'):
                        if '[폴더] ' in text:
                            version_folders[key].append(text.replace(f'[{vname}][폴더] ', ''))
                        elif '[파일] ' in text:
                            version_files[key].append(text.replace(f'[{vname}][파일] ', ''))
                        break
            for key in VERSION_ORDER:
                self.settings.set_version_backup_folders(key, version_folders[key])
                self.settings.set_version_backup_files(key, version_files[key])

            self.settings.save_config()
        except Exception:
            pass

    def load_settings(self):
        self._on_version_combo_changed(0)
        self._refresh_backup_folder_label()

        forever_map = self.settings.get_account_forever_map()
        if forever_map:
            self._account_names = list(forever_map)
        else:
            names = self.settings.get_account_names()
            if not names:
                single = self.settings.get_account_name()
                if single:
                    names = [single]
            self._account_names = [{'main': n, 'forever': None} for n in names]

        self._rebuild_account_tags()
        self.load_backup_list()

    def load_backup_list(self):
        self.backup_list.clear()
        for version in VERSION_ORDER:
            vname = self.settings.get_game_version_name(version)
            for folder in self.settings.get_version_backup_folders(version):
                self.backup_list.addItem(f'[{vname}][폴더] {folder}')
            for file in self.settings.get_version_backup_files(version):
                self.backup_list.addItem(f'[{vname}][파일] {file}')

    def browse_path(self, version):
        idx = VERSION_ORDER.index(version) if version in VERSION_ORDER else 0
        self.version_combo.setCurrentIndex(idx)
        self._browse_game_path()

    def validate_game_path(self, path):
        return any((Path(path) / exe).exists()
                   for exe in ('Wow.exe', 'WowClassic.exe', 'WowClassicEra.exe'))
