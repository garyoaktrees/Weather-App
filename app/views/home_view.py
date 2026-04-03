from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import (
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QPlainTextEdit,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from app.core.paths import ALERT_ICONS_DIR
from app.widgets.radar_widget import RadarWidget
from app.widgets.weather_card import WeatherCard


class HomeView(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self.view_mode = "modern"

        self.root = QVBoxLayout(self)
        self.root.setContentsMargins(16, 16, 16, 16)
        self.root.setSpacing(14)

        self.title_label = QLabel("The Weather App V2")
        self.title_label.setStyleSheet("font-size: 30px; font-weight: 900; color: white;")

        self.subtitle_label = QLabel("Search for a city, state, or ZIP to begin.")
        self.subtitle_label.setStyleSheet("font-size: 15px; color: #d7e3ff;")

        self.root.addWidget(self.title_label)
        self.root.addWidget(self.subtitle_label)

        self.stack = QStackedWidget()
        self.root.addWidget(self.stack, 1)

        self.modern_page = QWidget()
        self.classic_page = QWidget()

        self.stack.addWidget(self.modern_page)
        self.stack.addWidget(self.classic_page)

        self._build_modern_page()
        self._build_classic_page()

        self.set_view_mode("modern")

    def _build_modern_page(self) -> None:
        layout = QVBoxLayout(self.modern_page)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(14)

        grid = QGridLayout()
        grid.setHorizontalSpacing(14)
        grid.setVerticalSpacing(14)

        self.weather_card = WeatherCard()
        self.radar_widget = RadarWidget()

        self.forecast_panel = self._make_modern_panel("5 DAY FORECAST")
        self.forecast_layout = self.forecast_panel.layout()

        self.hourly_panel = self._make_modern_panel("24 HOUR FORECAST")
        self.hourly_layout = self.hourly_panel.layout()

        self.alert_panel = self._make_modern_panel("ALERTS")
        self.alert_panel_layout = self.alert_panel.layout()

        self.alert_icon_label = QLabel()
        self.alert_icon_label.setFixedSize(36, 36)
        self.alert_icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.alert_text = QPlainTextEdit()
        self.alert_text.setReadOnly(True)
        self.alert_text.setMinimumHeight(160)

        alert_header_row = QHBoxLayout()
        alert_header_row.addWidget(self.alert_icon_label)
        alert_header_row.addStretch()

        self.alert_panel_layout.addLayout(alert_header_row)
        self.alert_panel_layout.addWidget(self.alert_text)

        self.forecast_rows = []
        for _ in range(5):
            row = self._make_forecast_row()
            self.forecast_layout.addWidget(row["frame"])
            self.forecast_rows.append(row)

        self.forecast_layout.addStretch()

        self.hourly_rows = []
        for _ in range(24):
            row = self._make_hourly_row()
            self.hourly_layout.addWidget(row["frame"])
            self.hourly_rows.append(row)

        self.hourly_layout.addStretch()

        grid.addWidget(self.weather_card, 0, 0)
        grid.addWidget(self.radar_widget, 0, 1)
        grid.addWidget(self.forecast_panel, 1, 0)
        grid.addWidget(self.hourly_panel, 1, 1)

        grid.setColumnStretch(0, 1)
        grid.setColumnStretch(1, 1)

        layout.addLayout(grid)
        layout.addWidget(self.alert_panel)

    def _build_classic_page(self) -> None:
        layout = QVBoxLayout(self.classic_page)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)

        self.classic_title_label = QLabel("THE WEATHER CHANNEL")
        self.classic_title_label.setAlignment(Qt.AlignCenter)
        self.classic_title_label.setStyleSheet("""
            QLabel {
                color: yellow;
                background: #001f4d;
                font-size: 30px;
                font-weight: 900;
                padding: 8px;
                font-family: "Courier New";
            }
        """)
        layout.addWidget(self.classic_title_label)

        self.classic_subtitle_label = QLabel("Get your accurate weather report brought to you by Gary")
        self.classic_subtitle_label.setAlignment(Qt.AlignCenter)
        self.classic_subtitle_label.setStyleSheet("""
            QLabel {
                color: cyan;
                background: #001f4d;
                font-size: 18px;
                font-weight: 900;
                padding: 4px;
                font-family: "Courier New";
            }
        """)
        layout.addWidget(self.classic_subtitle_label)

        display_grid = QGridLayout()
        display_grid.setHorizontalSpacing(16)
        display_grid.setVerticalSpacing(8)

        self.classic_radar_widget = RadarWidget()
        self.classic_report_text = QPlainTextEdit()
        self.classic_report_text.setReadOnly(True)
        self.classic_report_text.setPlainText("Awaiting location input...")

        display_grid.addWidget(self.classic_radar_widget, 0, 0)
        display_grid.addWidget(self.classic_report_text, 0, 1)

        display_grid.setColumnStretch(0, 1)
        display_grid.setColumnStretch(1, 1)

        layout.addLayout(display_grid, 1)

        self.classic_status_label = QLabel("Ready.")
        self.classic_status_label.setStyleSheet("""
            QLabel {
                color: white;
                background: #003366;
                font-size: 13px;
                font-weight: 900;
                padding: 8px 10px;
                border: 2px solid cyan;
                font-family: "Courier New";
            }
        """)
        layout.addWidget(self.classic_status_label)

        self.classic_ticker_label = QLabel(" Enter a location to load your local weather ticker... ")
        self.classic_ticker_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        self.classic_ticker_label.setStyleSheet("""
            QLabel {
                color: black;
                background: yellow;
                font-size: 14px;
                font-weight: 900;
                padding: 8px 10px;
                border: 2px solid #003366;
                font-family: "Courier New";
            }
        """)
        layout.addWidget(self.classic_ticker_label)

    def _make_modern_panel(self, title: str) -> QFrame:
        panel = QFrame()
        panel.setStyleSheet("""
            QFrame {
                background-color: rgba(16, 43, 82, 0.88);
                border: 2px solid #35598f;
                border-radius: 18px;
            }
        """)
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)

        header = QLabel(title)
        header.setObjectName("SectionTitle")
        header.setAlignment(Qt.AlignCenter)
        layout.addWidget(header)

        return panel

    def _make_forecast_row(self) -> dict:
        frame = QFrame()
        frame.setStyleSheet("""
            QFrame {
                background-color: rgba(255, 255, 255, 6);
                border: 1px solid rgba(255, 255, 255, 45);
                border-radius: 10px;
            }
        """)
        layout = QHBoxLayout(frame)
        layout.setContentsMargins(10, 8, 10, 8)
        layout.setSpacing(10)

        day = QLabel("---")
        icon = QLabel()
        icon.setFixedSize(34, 34)
        icon.setAlignment(Qt.AlignCenter)
        condition = QLabel("No data")
        temp = QLabel("--° / --°")

        day.setMinimumWidth(60)
        temp.setMinimumWidth(105)

        layout.addWidget(day)
        layout.addWidget(icon)
        layout.addWidget(condition, 1)
        layout.addWidget(temp)

        return {
            "frame": frame,
            "day": day,
            "icon": icon,
            "condition": condition,
            "temp": temp,
        }

    def _make_hourly_row(self) -> dict:
        frame = QFrame()
        frame.setStyleSheet("""
            QFrame {
                background-color: rgba(255, 255, 255, 4);
                border: 1px solid rgba(255, 255, 255, 40);
                border-radius: 10px;
            }
        """)
        layout = QHBoxLayout(frame)
        layout.setContentsMargins(10, 8, 10, 8)
        layout.setSpacing(10)

        time = QLabel("---")
        icon = QLabel()
        icon.setFixedSize(28, 28)
        icon.setAlignment(Qt.AlignCenter)
        condition = QLabel("No data")
        temp = QLabel("--°")

        time.setMinimumWidth(70)
        temp.setMinimumWidth(70)

        layout.addWidget(time)
        layout.addWidget(icon)
        layout.addWidget(condition, 1)
        layout.addWidget(temp)

        return {
            "frame": frame,
            "time": time,
            "icon": icon,
            "condition": condition,
            "temp": temp,
        }

    def set_view_mode(self, mode: str) -> None:
        self.view_mode = mode
        self.stack.setCurrentWidget(self.classic_page if mode == "classic" else self.modern_page)
        self.weather_card.set_view_mode(mode)
        self.radar_widget.set_view_mode(mode)
        self.classic_radar_widget.set_view_mode("classic")

    def update_weather_card(
        self,
        location_name: str,
        temperature: str,
        condition_text: str,
        feels_like_text: str,
        humidity_text: str,
        wind_text: str,
        aqi_text: str,
        icon_filename: str,
        updated_text: str,
    ) -> None:
        self.weather_card.update_weather(
            location_name=location_name,
            temperature=temperature,
            condition_text=condition_text,
            feels_like_text=feels_like_text,
            humidity_text=humidity_text,
            wind_text=wind_text,
            aqi_text=aqi_text,
            icon_filename=icon_filename,
            updated_text=updated_text,
        )

    def clear_conditions(self, message: str = "Weather unavailable") -> None:
        self.weather_card.clear_weather(message)
        self.classic_report_text.setPlainText("Awaiting location input...")

    def update_forecast_rows(self, rows: list[dict]) -> None:
        for i, row_data in enumerate(rows):
            if i >= len(self.forecast_rows):
                break

            row = self.forecast_rows[i]
            row["day"].setText(row_data["day"])
            row["condition"].setText(row_data["condition"])
            row["temp"].setText(row_data["temp"])
            self._set_icon(row["icon"], row_data["icon"], 32)

    def update_hourly_rows(self, rows: list[dict]) -> None:
        for i, row_data in enumerate(rows):
            if i >= len(self.hourly_rows):
                break

            row = self.hourly_rows[i]
            row["time"].setText(row_data["time"])
            row["condition"].setText(row_data["condition"])
            row["temp"].setText(row_data["temp"])
            self._set_icon(row["icon"], row_data["icon"], 28)

    def set_alerts(self, alerts: list[dict]) -> None:
        if not alerts:
            self.alert_text.setPlainText("No active alerts reported for this location.")
            self._set_alert_icon("info.png")
            return

        blocks = []
        for alert in alerts[:5]:
            lines = [
                f"{alert.get('event', 'Alert')} [{alert.get('severity', 'Unknown')}]",
                alert.get("headline", ""),
            ]
            if alert.get("instruction"):
                lines.append(f"Instructions: {alert['instruction']}")
            blocks.append("\n".join([x for x in lines if x]))

        self.alert_text.setPlainText("\n\n".join(blocks))
        self._set_alert_icon(self._highest_alert_icon(alerts))

    def set_classic_report(self, text: str) -> None:
        self.classic_report_text.setPlainText(text)
        self.classic_report_text.verticalScrollBar().setValue(0)

    def set_classic_status(self, text: str) -> None:
        self.classic_status_label.setText(text)

    def set_ticker_text(self, text: str) -> None:
        self.classic_ticker_label.setText(text)

    def set_radar_location(self, lat: float, lon: float) -> None:
        self.radar_widget.set_location(lat, lon)
        self.classic_radar_widget.set_location(lat, lon)

    def set_radar_visible(self, enabled: bool) -> None:
        self.radar_widget.setVisible(enabled)
        self.classic_radar_widget.setVisible(enabled)

    def _set_alert_icon(self, filename: str) -> None:
        path = ALERT_ICONS_DIR / filename
        pixmap = QPixmap(str(path))
        if pixmap.isNull():
            self.alert_icon_label.clear()
            return

        self.alert_icon_label.setPixmap(
            pixmap.scaled(
                30,
                30,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
        )

    def _highest_alert_icon(self, alerts: list[dict]) -> str:
        best_rank = 0
        best_icon = "info.png"

        for alert in alerts:
            event = str(alert.get("event", "")).lower()
            severity = str(alert.get("severity", "")).lower()

            rank = 1
            icon = "info.png"

            if "warning" in event or severity in {"extreme", "severe"}:
                rank = 4
                icon = "warning.png"
            elif "watch" in event:
                rank = 3
                icon = "watch.png"
            elif "advisory" in event or severity in {"moderate", "minor"}:
                rank = 2
                icon = "advisory.png"

            if rank > best_rank:
                best_rank = rank
                best_icon = icon

        return best_icon

    def _set_icon(self, label: QLabel, filename: str, size: int) -> None:
        from app.core.paths import ICONS_DIR

        path = ICONS_DIR / filename
        pixmap = QPixmap(str(path))
        if pixmap.isNull():
            label.clear()
            return

        label.setPixmap(
            pixmap.scaled(
                size,
                size,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
        )