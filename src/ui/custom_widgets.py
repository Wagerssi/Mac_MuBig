"""
커스텀 위젯 정의
외곽선 효과가 있는 버튼 등 커스텀 UI 위젯
"""

from PySide6.QtWidgets import QPushButton, QStyleOptionButton, QStyle
from PySide6.QtCore import Qt
from PySide6.QtGui import QPainter, QPen, QColor, QBrush, QFont


class OutlinedButton(QPushButton):
    """
    hover 동작:
      - 배경이 짙은 색(어두운 남색)으로 변함
      - 황금색 테두리(#ffd232) 로 강조
      - 텍스트도 황금색으로 변함
    기본 배경색은 setNormalColor() 로 외부에서 지정 가능
    """

    _DEFAULT_BG = '#4a9eff'   # 기본 파란색

    def __init__(self, text="", parent=None):
        super().__init__(text, parent)
        self.setMouseTracking(True)
        self._hovered = False
        self._normal_bg = QColor(self._DEFAULT_BG)

    # ── 외부에서 기본 배경색 지정 ──────────────────────────────
    def setNormalColor(self, color_hex: str):
        self._normal_bg = QColor(color_hex)
        self.update()

    # 이전 버전 호환용 stub
    def set_colors(self, normal=None, hover=None):
        if normal is not None:
            self._normal_bg = QColor(normal) if isinstance(normal, str) else normal
            self.update()

    # ── hover 추적 ──────────────────────────────────────────────
    def enterEvent(self, event):
        self._hovered = True
        self.update()
        super().enterEvent(event)

    def leaveEvent(self, event):
        self._hovered = False
        self.update()
        super().leaveEvent(event)

    # ── 그리기 ─────────────────────────────────────────────────
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        rect   = self.rect()
        radius = 4

        if not self.isEnabled():
            bg       = QColor(80, 80, 80)
            border   = QColor(100, 100, 100)
            border_w = 1
        elif self.isDown():
            bg       = QColor(15, 25, 55)
            border   = QColor(255, 210, 50)
            border_w = 2
        elif self._hovered:
            # ★ hover: 짙은 남색 배경 + 황금 테두리
            bg       = QColor(20, 30, 65)
            border   = QColor(255, 210, 50)
            border_w = 2
        else:
            bg       = self._normal_bg
            border   = self._normal_bg.darker(160)
            border_w = 1

        # 배경
        painter.setPen(Qt.NoPen)
        painter.setBrush(QBrush(bg))
        painter.drawRoundedRect(rect, radius, radius)

        # 테두리
        painter.setPen(QPen(border, border_w))
        painter.setBrush(Qt.NoBrush)
        painter.drawRoundedRect(rect.adjusted(1, 1, -1, -1), radius, radius)

        # ── 텍스트 ──────────────────────────────────────────────
        option = QStyleOptionButton()
        option.initFrom(self)
        option.text = ""
        text_rect = self.style().subElementRect(
            QStyle.SE_PushButtonContents, option, self)

        font = QFont(self.font())
        font.setBold(True)
        painter.setFont(font)
        fm = painter.fontMetrics()

        x = text_rect.x() + (text_rect.width()  - fm.horizontalAdvance(self.text())) / 2
        y = text_rect.y() + (text_rect.height()  + fm.ascent() - fm.descent()) / 2

        # 외곽선 색
        outline = QColor(20, 20, 20)
        painter.setPen(QPen(outline, 2))
        for dx, dy in [(-1,-1),(1,-1),(-1,1),(1,1)]:
            painter.drawText(x+dx, y+dy, self.text())

        # 텍스트 색: hover → 황금, 비활성 → 회색, 기본 → 흰색 고정
        if not self.isEnabled():
            text_color = QColor(140, 140, 140)
        elif self._hovered or self.isDown():
            text_color = QColor(255, 220, 50)   # 황금
        else:
            text_color = QColor(255, 255, 255)  # 항상 흰색

        painter.setPen(QPen(text_color, 1))
        painter.drawText(x, y, self.text())

        painter.end()
