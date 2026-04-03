from __future__ import annotations

from PySide6.QtCore import QObject, Signal, Slot

from app.services.weather_api import WeatherAPI


class WeatherWorker(QObject):
    finished = Signal(dict)
    failed = Signal(str)

    def __init__(self, location_query: str) -> None:
        super().__init__()
        self.location_query = location_query
        self.weather_api = WeatherAPI()

    @Slot()
    def run(self) -> None:
        try:
            payload = self.weather_api.get_weather(self.location_query)
            self.finished.emit(payload)
        except Exception as exc:
            self.failed.emit(str(exc))