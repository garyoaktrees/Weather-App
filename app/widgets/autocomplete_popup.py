from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QListWidget, QListWidgetItem


class AutocompletePopup(QListWidget):
    location_chosen = Signal(dict)

    def __init__(self, parent=None) -> None:
        super().__init__(parent)

        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.Tool
        )
        self.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setVerticalScrollMode(QListWidget.ScrollMode.ScrollPerPixel)

        self.setStyleSheet("""
            QListWidget {
                background-color: #102b52;
                border: 2px solid #3f6fb6;
                border-radius: 8px;
                padding: 4px;
                color: white;
                outline: none;
            }
            QListWidget::item {
                padding: 8px 10px;
                border-radius: 6px;
            }
            QListWidget::item:selected {
                background-color: #1c467d;
                color: white;
            }
            QListWidget::item:hover {
                background-color: #163860;
            }
        """)

        self.itemClicked.connect(self._handle_item_clicked)

    def show_suggestions(self, items: list[dict], global_pos, width: int) -> None:
        self.clear()

        for location in items:
            label = location.get("display_name", "Unknown")
            zip_code = location.get("zip", "")

            if zip_code:
                label = f"{label} ({zip_code})"

            item = QListWidgetItem(label)
            item.setData(Qt.ItemDataRole.UserRole, location)
            self.addItem(item)

        if not items:
            self.hide()
            return

        self.setFixedWidth(width)
        row_height = 34
        visible_rows = min(len(items), 6)
        self.setFixedHeight((visible_rows * row_height) + 8)
        self.move(global_pos)
        self.setCurrentRow(0)
        self.show()

    def _handle_item_clicked(self, item: QListWidgetItem) -> None:
        data = item.data(Qt.ItemDataRole.UserRole)
        if isinstance(data, dict):
            self.location_chosen.emit(data)
        self.hide()

    def choose_current(self) -> dict | None:
        item = self.currentItem()
        if item is None:
            return None

        data = item.data(Qt.ItemDataRole.UserRole)
        self.hide()
        return data if isinstance(data, dict) else None