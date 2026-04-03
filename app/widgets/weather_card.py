from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import QFrame, QLabel, QVBoxLayout, QHBoxLayout

from app.core.paths import ICONS_DIR


class WeatherCard(QFrame):
    def __init__(self) -> None:
        super().__init__()
        self.setObjectName("WeatherCard")
        self.view_mode = "modern"

        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(20, 18, 20, 18)
        root_layout.setSpacing(12)

        self.location_label = QLabel("No location selected")
        self.location_label.setObjectName("SectionTitle")

        self.updated_label = QLabel("")
        self.updated_label.setStyleSheet("font-size: 12px; color: #c9dbff;")

        middle_row = QHBoxLayout()
        middle_row.setSpacing(24)

        self.icon_label = QLabel()
        self.icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.icon_label.setFixedSize(96, 96)

        self.temp_label = QLabel("--°F")
        self.temp_label.setStyleSheet("font-size: 46px; font-weight: 900; color: white;")

        middle_row.addWidget(self.icon_label)
        middle_row.addWidget(self.temp_label)
        middle_row.addStretch()

        self.condition_label = QLabel("Condition unavailable")
        self.condition_label.setStyleSheet("font-size: 18px; font-weight: 800;")

        self.feels_like_label = QLabel("Feels Like: --°F")
        self.feels_like_label.setStyleSheet("font-size: 15px; color: #d7e3ff;")

        self.humidity_label = QLabel("Humidity: --%")
        self.humidity_label.setStyleSheet("font-size: 15px; color: #d7e3ff;")

        self.wind_label = QLabel("Wind: -- mph")
        self.wind_label.setStyleSheet("font-size: 15px; color: #d7e3ff;")

        self.aqi_label = QLabel("Air Quality: --")
        self.aqi_label.setStyleSheet("font-size: 15px; color: #d7e3ff;")

        root_layout.addWidget(self.location_label)
        root_layout.addWidget(self.updated_label)
        root_layout.addLayout(middle_row)
        root_layout.addWidget(self.condition_label)
        root_layout.addWidget(self.feels_like_label)
        root_layout.addWidget(self.humidity_label)
        root_layout.addWidget(self.wind_label)
        root_layout.addWidget(self.aqi_label)

        self._set_icon("cloudy.png")
        self.set_view_mode("modern")

    def set_view_mode(self, mode: str) -> None:
        self.view_mode = mode
        if mode == "classic":
            self.setStyleSheet("""
                QFrame#WeatherCard {
                    background-color: rgba(20, 54, 96, 0.98);
                    border: 2px solid #4f84d9;
                    border-radius: 6px;
                }
                QLabel {
                    color: white;
                    font-family: "Courier New";
                }
            """)
        else:
            self.setStyleSheet("""
                QFrame#WeatherCard {
                    background-color: rgba(16, 43, 82, 0.88);
                    border: 2px solid #35598f;
                    border-radius: 18px;
                }
                QLabel {
                    color: white;
                }
            """)

    def _set_icon(self, filename: str) -> None:
        icon_path = ICONS_DIR / filename

        if not icon_path.exists():
            self.icon_label.setText("?")
            self.icon_label.setPixmap(QPixmap())
            return

        pixmap = QPixmap(str(icon_path))
        if pixmap.isNull():
            self.icon_label.setText("?")
            self.icon_label.setPixmap(QPixmap())
            return

        scaled = pixmap.scaled(
            96,
            96,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )
        self.icon_label.setText("")
        self.icon_label.setPixmap(scaled)

    def update_weather(
        self,
        location_name: str,
        temperature: str,
        condition_text: str,
        feels_like_text: str,
        humidity_text: str,
        wind_text: str,
        aqi_text: str,
        icon_filename: str,
        updated_text: str = "",
    ) -> None:
        self.location_label.setText(location_name)
        self.temp_label.setText(temperature)
        self.condition_label.setText(condition_text)
        self.feels_like_label.setText(feels_like_text)
        self.humidity_label.setText(humidity_text)
        self.wind_label.setText(wind_text)
        self.aqi_label.setText(aqi_text)
        self.updated_label.setText(updated_text)
        self._set_icon(icon_filename)

    def clear_weather(self, message: str = "Weather unavailable") -> None:
        self.location_label.setText(message)
        self.temp_label.setText("--°F")
        self.condition_label.setText("Condition unavailable")
        self.feels_like_label.setText("Feels Like: --°F")
        self.humidity_label.setText("Humidity: --%")
        self.wind_label.setText("Wind: -- mph")
        self.aqi_label.setText("Air Quality: --")
        self.updated_label.setText("")
        self._set_icon("cloudy.png")