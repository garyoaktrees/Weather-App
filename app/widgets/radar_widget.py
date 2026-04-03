from __future__ import annotations

from PySide6.QtCore import QUrl, Qt
from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget

try:
    from PySide6.QtWebEngineWidgets import QWebEngineView
except Exception:
    QWebEngineView = None


class RadarWidget(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self.latitude: float | None = None
        self.longitude: float | None = None
        self.view_mode = "modern"

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        self.header_label = QLabel("Radar")
        self.header_label.setObjectName("SectionTitle")
        layout.addWidget(self.header_label)

        if QWebEngineView is not None:
            self.web_view = QWebEngineView()
            self.web_view.setMinimumHeight(300)
            layout.addWidget(self.web_view)
        else:
            self.web_view = None
            self.placeholder = QLabel("Qt WebEngine is unavailable. Radar cannot be shown.")
            self.placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.placeholder.setMinimumHeight(300)
            layout.addWidget(self.placeholder)

        self.set_view_mode("modern")

    def set_view_mode(self, mode: str) -> None:
        self.view_mode = mode
        if mode == "classic":
            self.setStyleSheet("""
                QWidget {
                    background-color: rgba(20, 54, 96, 0.98);
                    border: 2px solid #4f84d9;
                    border-radius: 6px;
                }
                QLabel {
                    color: white;
                    padding: 6px 10px;
                    font-family: "Courier New";
                }
            """)
        else:
            self.setStyleSheet("""
                QWidget {
                    background-color: rgba(16, 43, 82, 0.88);
                    border: 2px solid #35598f;
                    border-radius: 18px;
                }
                QLabel {
                    color: white;
                    padding: 8px 12px;
                }
            """)

    def set_location(self, lat: float, lon: float) -> None:
        self.latitude = lat
        self.longitude = lon
        self.refresh()

    def refresh(self) -> None:
        if self.web_view is None or self.latitude is None or self.longitude is None:
            return

        lat = self.latitude
        lon = self.longitude

        url = (
            "https://embed.windy.com/embed2.html"
            f"?lat={lat}&lon={lon}&detailLat={lat}&detailLon={lon}"
            "&width=650&height=450&zoom=7&level=surface"
            "&overlay=radar&product=radar&menu=&message=true&marker=true"
        )
        self.web_view.setUrl(QUrl(url))