from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QSlider,
    QVBoxLayout,
)


class SettingsDialog(QDialog):
    def __init__(self, settings: dict, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Settings")
        self.setModal(True)
        self.resize(430, 320)

        root = QVBoxLayout(self)

        form = QFormLayout()
        form.setSpacing(12)

        self.home_location_edit = QLineEdit(settings.get("home_location", ""))

        self.ui_mode_combo = QComboBox()
        self.ui_mode_combo.addItems(["modern", "classic"])
        self.ui_mode_combo.setCurrentText(settings.get("ui_mode", "modern"))

        self.music_checkbox = QCheckBox("Enable background music")
        self.music_checkbox.setChecked(bool(settings.get("music_enabled", True)))

        self.radar_checkbox = QCheckBox("Enable radar panel")
        self.radar_checkbox.setChecked(bool(settings.get("radar_enabled", True)))

        self.description_combo = QComboBox()
        self.description_combo.addItems(["funny", "normal"])
        self.description_combo.setCurrentText(settings.get("description_mode", "funny"))

        self.volume_slider = QSlider(Qt.Orientation.Horizontal)
        self.volume_slider.setRange(0, 100)
        self.volume_slider.setValue(int(settings.get("music_volume", 35)))

        volume_row = QHBoxLayout()
        volume_row.addWidget(self.volume_slider)
        self.volume_value = QLabel(f"{self.volume_slider.value()}%")
        volume_row.addWidget(self.volume_value)

        self.volume_slider.valueChanged.connect(
            lambda value: self.volume_value.setText(f"{value}%")
        )

        self.ticker_speed_combo = QComboBox()
        self.ticker_speed_combo.addItems(["60", "80", "100", "120", "150", "180"])
        current_speed = str(int(settings.get("ticker_speed_ms", 120)))
        if self.ticker_speed_combo.findText(current_speed) == -1:
            self.ticker_speed_combo.addItem(current_speed)
        self.ticker_speed_combo.setCurrentText(current_speed)

        form.addRow("Home location:", self.home_location_edit)
        form.addRow("View mode:", self.ui_mode_combo)
        form.addRow("Description mode:", self.description_combo)
        form.addRow("Ticker speed (ms):", self.ticker_speed_combo)
        form.addRow("", self.music_checkbox)
        form.addRow("", self.radar_checkbox)
        form.addRow("Music volume:", volume_row)

        root.addLayout(form)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save
            | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        root.addWidget(buttons)

    def get_settings(self) -> dict:
        return {
            "home_location": self.home_location_edit.text().strip(),
            "ui_mode": self.ui_mode_combo.currentText(),
            "music_enabled": self.music_checkbox.isChecked(),
            "radar_enabled": self.radar_checkbox.isChecked(),
            "music_volume": self.volume_slider.value(),
            "description_mode": self.description_combo.currentText(),
            "ticker_speed_ms": int(self.ticker_speed_combo.currentText()),
        }