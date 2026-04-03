from __future__ import annotations

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QFont
from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget


class LoadingSpinner(QWidget):
    def __init__(self) -> None:
        super().__init__()

        self.frames = ["☀️", "🌤️", "⛅", "🌥️", "☁️", "🌥️", "⛅", "🌤️"]
        self.current_index = 0

        self.icon_label = QLabel(self.frames[0])
        self.icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.icon_label.setFont(QFont("Segoe UI Emoji", 28))

        self.text_label = QLabel("Loading weather...")
        self.text_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.text_label.setStyleSheet(
            "font-size: 18px; font-weight: 700; color: #ffd400;"
        )

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(6)
        layout.addWidget(self.icon_label)
        layout.addWidget(self.text_label)

        self.setStyleSheet("""
            QWidget {
                background-color: rgba(16, 43, 82, 0.90);
                border: 2px solid #3f6fb6;
                border-radius: 10px;
            }
        """)

        self.timer = QTimer(self)
        self.timer.timeout.connect(self._advance_frame)
        self.timer.setInterval(120)

    def _advance_frame(self) -> None:
        self.current_index = (self.current_index + 1) % len(self.frames)
        self.icon_label.setText(self.frames[self.current_index])

    def start(self) -> None:
        self.current_index = 0
        self.icon_label.setText(self.frames[self.current_index])
        self.show()
        self.timer.start()

    def stop(self) -> None:
        self.timer.stop()
        self.hide()