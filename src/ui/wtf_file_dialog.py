"""
WTF 파일 선택 다이얼로그
SavedVariables 폴더의 파일을 선택하는 다이얼로그
"""

import zipfile
from pathlib import Path
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout,
    QPushButton, QListWidget, QListWidgetItem,
    QLabel, QCheckBox, QDialogButtonBox,
    QAbstractItemView
)
from PySide6.QtCore import Qt

class WTFFileDialog(QDialog):
    """WTF 파일 선택 다이얼로그"""

    def __init__(self, zip_path: str, parent=None):
        super().__init__(parent)
        self.zip_path = zip_path
        self.selected_files = []
        self.setup_ui()
        self.load_files()

    def setup_ui(self):
        """UI 초기화"""
        self.setWindowTitle("WTF 파일 선택")
        self.setMinimumSize(500, 400)

        layout = QVBoxLayout()

        # 설명 레이블
        info_label = QLabel("설치할 SavedVariables 파일을 선택하세요:")
        layout.addWidget(info_label)

        # 파일 리스트
        self.file_list = QListWidget()
        self.file_list.setSelectionMode(QAbstractItemView.MultiSelection)
        layout.addWidget(self.file_list)

        # 전체 선택/해제 버튼
        button_layout = QHBoxLayout()
        self.select_all_btn = QPushButton("전체 선택")
        self.select_all_btn.clicked.connect(self.select_all)
        self.deselect_all_btn = QPushButton("전체 해제")
        self.deselect_all_btn.clicked.connect(self.deselect_all)
        button_layout.addWidget(self.select_all_btn)
        button_layout.addWidget(self.deselect_all_btn)
        button_layout.addStretch()
        layout.addLayout(button_layout)

        # 다이얼로그 버튼
        self.button_box = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        )
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        layout.addWidget(self.button_box)

        self.setLayout(layout)

    def load_files(self):
        """ZIP 파일에서 SavedVariables 파일 목록 로드"""
        try:
            with zipfile.ZipFile(self.zip_path, 'r') as zip_ref:
                # SavedVariables 폴더 찾기
                saved_vars_files = []
                for file_name in zip_ref.namelist():
                    if "SavedVariables/" in file_name and file_name.endswith(".lua"):
                        # .bak 파일은 제외
                        if not file_name.endswith(".lua.bak"):
                            # 파일명만 추출
                            file_only = Path(file_name).name
                            if file_only not in saved_vars_files:
                                saved_vars_files.append(file_only)

                # 리스트에 추가
                for file_name in sorted(saved_vars_files):
                    item = QListWidgetItem(file_name)
                    item.setData(Qt.UserRole, file_name)
                    self.file_list.addItem(item)

        except Exception as e:
            print(f"파일 로드 오류: {str(e)}")

    def select_all(self):
        """전체 선택"""
        for i in range(self.file_list.count()):
            item = self.file_list.item(i)
            item.setSelected(True)

    def deselect_all(self):
        """전체 해제"""
        for i in range(self.file_list.count()):
            item = self.file_list.item(i)
            item.setSelected(False)

    def get_selected_files(self) -> list:
        """선택된 파일 목록 반환"""
        selected = []
        for item in self.file_list.selectedItems():
            selected.append(item.data(Qt.UserRole))
        return selected