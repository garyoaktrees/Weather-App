from __future__ import annotations

from PySide6.QtCore import QPoint, QEvent, QTimer, Qt, Signal
from PySide6.QtGui import QKeyEvent
from PySide6.QtWidgets import QHBoxLayout, QLineEdit, QPushButton, QWidget

from app.services.location_service import LocationService
from app.widgets.autocomplete_popup import AutocompletePopup


class SearchBar(QWidget):
    search_submitted = Signal(str)
    location_selected = Signal(dict)

    def __init__(self) -> None:
        super().__init__()

        self.location_service = LocationService()
        self.popup = AutocompletePopup()

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Enter city, state, or ZIP...")
        self.search_input.returnPressed.connect(self._handle_return_pressed)

        self.search_button = QPushButton("Search")
        self.search_button.clicked.connect(self.emit_search)

        layout.addWidget(self.search_input, 1)
        layout.addWidget(self.search_button)

        self.search_input.textEdited.connect(self._on_text_edited)
        self.popup.location_chosen.connect(self._on_location_chosen)

        self._debounce_timer = QTimer(self)
        self._debounce_timer.setSingleShot(True)
        self._debounce_timer.timeout.connect(self._run_autocomplete)

        self.search_input.installEventFilter(self)

    def _on_text_edited(self, _text: str) -> None:
        self._debounce_timer.start(180)

    def _run_autocomplete(self) -> None:
        query = self.search_input.text().strip()
        if len(query) < 2:
            self.popup.hide()
            return

        results = self.location_service.autocomplete(query)
        items = [result.to_dict() for result in results]

        if not items:
            self.popup.hide()
            return

        below_input = self.search_input.mapToGlobal(QPoint(0, self.search_input.height() + 2))
        self.popup.show_suggestions(items, below_input, self.search_input.width())

        self.search_input.setFocus()
        self.search_input.setCursorPosition(len(self.search_input.text()))

    def _on_location_chosen(self, location: dict) -> None:
        display_name = location.get("display_name", "")
        if display_name:
            self.search_input.setText(display_name)

        self.search_input.setFocus()
        self.search_input.setCursorPosition(len(self.search_input.text()))

        self.location_selected.emit(location)
        self.emit_search()

    def _handle_return_pressed(self) -> None:
        if self.popup.isVisible():
            selected = self.popup.choose_current()
            if selected:
                self._on_location_chosen(selected)
                return

        self.emit_search()

    def emit_search(self) -> None:
        query = self.search_input.text().strip()
        if query:
            self.popup.hide()
            self.search_input.setFocus()
            self.search_submitted.emit(query)

    def eventFilter(self, obj, event) -> bool:
        if obj is self.search_input and event.type() == QEvent.Type.KeyPress:
            if isinstance(event, QKeyEvent) and self.popup.isVisible():
                key = event.key()

                if key == Qt.Key.Key_Down:
                    current = self.popup.currentRow()
                    self.popup.setCurrentRow(min(current + 1, self.popup.count() - 1))
                    return True

                if key == Qt.Key.Key_Up:
                    current = self.popup.currentRow()
                    self.popup.setCurrentRow(max(current - 1, 0))
                    return True

                if key == Qt.Key.Key_Escape:
                    self.popup.hide()
                    self.search_input.setFocus()
                    return True

        return super().eventFilter(obj, event)