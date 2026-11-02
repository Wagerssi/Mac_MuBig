"""
UI 스타일 정의
어플리케이션 전체 스타일시트 및 테마 설정
"""

# 어플리케이션 전체 스타일시트
APP_STYLESHEET = """
QMainWindow {
    background-color: #2b2b2b;
}

QTabWidget {
    background-color: #2b2b2b;
}

QTabWidget::pane {
    border: 1px solid #555;
    background-color: #3c3c3c;
    border-radius: 4px;
    padding: 10px;
}

QTabBar::tab {
    background-color: #3c3c3c;
    color: #ffffff;
    padding: 8px 20px;
    margin-right: 2px;
    border-top-left-radius: 4px;
    border-top-right-radius: 4px;
    font-weight: bold;
}

QTabBar::tab:selected {
    background-color: #4a9eff;
    color: #ffffff;
    font-weight: bold;
}

QTabBar::tab:hover {
    background-color: #555;
}

QPushButton {
    background-color: #4a9eff;
    color: white;
    border: 1px solid rgba(0, 0, 0, 0.3);
    padding: 8px 16px;
    border-radius: 4px;
    font-weight: bold;
    font-size: 13px;
    min-width: 80px;
}

QPushButton:hover {
    background-color: #6ec3ff;
    border: 1px solid #78cbff;
}

QPushButton:pressed {
    background-color: #2a7edf;
    border: 1px solid #1a6ecf;
}

QPushButton:disabled {
    background-color: #666;
    color: #999;
}

QPushButton.auth-button {
    min-width: 100px;
}

QPushButton.auth-success {
    background-color: #4caf50;
}

QPushButton.auth-failed {
    background-color: #f44336;
}

QPushButton.version-button {
    min-width: 120px;
}

QPushButton.version-button:hover {
    background-color: #777;
    border: 1px solid #999;
}

QLineEdit {
    background-color: #555;
    color: white;
    border: 1px solid #666;
    padding: 6px;
    border-radius: 4px;
}

QLineEdit:focus {
    border: 1px solid #4a9eff;
}

QLineEdit:disabled {
    background-color: #3c3c3c;
    color: #999;
}

QLabel {
    color: #ffffff;
    font-size: 12px;
}

QGroupBox {
    color: #ffffff;
    border: 1px solid #555;
    border-radius: 4px;
    margin-top: 10px;
    padding-top: 10px;
    font-weight: bold;
}

QGroupBox::title {
    subcontrol-origin: margin;
    left: 10px;
    padding: 0 5px 0 5px;
}

QProgressBar {
    background-color: #3c3c3c;
    border: 1px solid #555;
    border-radius: 4px;
    text-align: center;
    color: white;
}

QProgressBar::chunk {
    background-color: #4a9eff;
    border-radius: 3px;
}

QListWidget {
    background-color: #3c3c3c;
    color: white;
    border: 1px solid #555;
    border-radius: 4px;
    padding: 5px;
}

QListWidget::item {
    padding: 3px;
}

QListWidget::item:selected {
    background-color: #4a9eff;
}

QListWidget::item:hover {
    background-color: #555;
}

QTextEdit {
    background-color: #3c3c3c;
    color: white;
    border: 1px solid #555;
    border-radius: 4px;
    padding: 5px;
}

QScrollBar:vertical {
    background-color: #3c3c3c;
    width: 12px;
    border-radius: 6px;
}

QScrollBar::handle:vertical {
    background-color: #666;
    border-radius: 6px;
    min-height: 20px;
}

QScrollBar::handle:vertical:hover {
    background-color: #777;
}

QCheckBox {
    color: white;
}

QCheckBox::indicator {
    width: 15px;
    height: 15px;
}

QCheckBox::indicator:unchecked {
    background-color: #555;
    border: 1px solid #666;
    border-radius: 3px;
}

QCheckBox::indicator:checked {
    background-color: #4a9eff;
    border: 1px solid #4a9eff;
    border-radius: 3px;
}

QMessageBox {
    background-color: #3c3c3c;
    color: white;
}

QMessageBox QPushButton {
    min-width: 60px;
}
"""

# 색상 팔레트
COLORS = {
    'primary': '#4a9eff',
    'primary_hover': '#3a8eef',
    'primary_pressed': '#2a7edf',
    'success': '#4caf50',
    'error': '#f44336',
    'warning': '#ff9800',
    'bg_dark': '#2b2b2b',
    'bg_medium': '#3c3c3c',
    'bg_light': '#555',
    'text': '#ffffff',
    'text_disabled': '#999',
    'border': '#666'
}