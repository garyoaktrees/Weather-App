from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone

from PySide6.QtCore import Qt, QThread, QTimer, QUrl
from PySide6.QtGui import QCloseEvent
from PySide6.QtMultimedia import QAudioOutput, QMediaPlayer
from PySide6.QtWidgets import (
    QHBoxLayout,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from app.core.paths import BACKGROUNDS_DIR, CITIES_JSON, DEFAULT_BG_FILE, MUSIC_FILE, ensure_directories
from app.services.weather_api import WeatherAPI
from app.services.weather_worker import WeatherWorker
from app.styles.theme import build_stylesheet
from app.utils.helpers import safe_float
from app.utils.settings_manager import load_settings, save_settings
from app.views.home_view import HomeView
from app.widgets.loading_spinner import LoadingSpinner
from app.widgets.search_bar import SearchBar
from app.widgets.settings_dialog import SettingsDialog

FUNNY_WEATHER_CODES = {
    0: "It's Hella Nice Outside",
    1: "Little Clouds But Still Chill",
    2: "Kinda Cloudy",
    3: "Overcast",
    45: "Spooky Fog",
    48: "Silent Hill Fog",
    51: "Little Drizzle",
    53: "Little More Drizzle",
    55: "Big Drizzle",
    56: "Cold Drizzle",
    57: "BIG COLD Drizzle",
    61: "Little Rain",
    63: "Little More Rain",
    65: "Big Rain",
    66: "Freezy Rain",
    67: "Big Freezy Rain",
    71: "Little Snow",
    73: "Little More Snow",
    75: "BIG Snow",
    77: "Snow Drizzle",
    80: "It's Raining",
    81: "It's BIG Rain",
    82: "BIIIIGGG RAIN",
    85: "Snow Showers",
    86: "BLIZZARD",
    95: "Thunder",
    96: "Thunder with ice that falls from the sky",
    99: "BIIIIGGG Thunder with BIGG ice that falls from the sky",
}

NORMAL_WEATHER_CODES = {
    0: "Clear",
    1: "Mostly Clear",
    2: "Partly Cloudy",
    3: "Overcast",
    45: "Fog",
    48: "Dense Fog",
    51: "Light Drizzle",
    53: "Drizzle",
    55: "Heavy Drizzle",
    56: "Freezing Drizzle",
    57: "Heavy Freezing Drizzle",
    61: "Light Rain",
    63: "Rain",
    65: "Heavy Rain",
    66: "Freezing Rain",
    67: "Heavy Freezing Rain",
    71: "Light Snow",
    73: "Snow",
    75: "Heavy Snow",
    77: "Snow Grains",
    80: "Rain Showers",
    81: "Heavy Rain Showers",
    82: "Violent Rain Showers",
    85: "Snow Showers",
    86: "Heavy Snow Showers",
    95: "Thunderstorm",
    96: "Thunderstorm with Hail",
    99: "Severe Thunderstorm with Hail",
}

SHORT_TEXT = {
    "It's Hella Nice Outside": "Nice",
    "Little Clouds But Still Chill": "Partly Cloudy",
    "Kinda Cloudy": "Cloudy",
    "Spooky Fog": "Fog",
    "Silent Hill Fog": "Dense Fog",
    "Little Drizzle": "Drizzle",
    "Little More Drizzle": "Drizzle",
    "Big Drizzle": "Heavy Drizzle",
    "Cold Drizzle": "Freezing Drizzle",
    "BIG COLD Drizzle": "Freezing Drizzle",
    "Little Rain": "Light Rain",
    "Little More Rain": "Rain",
    "Big Rain": "Heavy Rain",
    "Freezy Rain": "Freezing Rain",
    "Big Freezy Rain": "Freezing Rain",
    "Little Snow": "Light Snow",
    "Little More Snow": "Snow",
    "BIG Snow": "Heavy Snow",
    "Snow Drizzle": "Snow",
    "It's Raining": "Rain",
    "It's BIG Rain": "Heavy Rain",
    "BIIIIGGG RAIN": "Severe Rain",
    "BLIZZARD": "Blizzard",
    "Thunder": "Thunderstorm",
    "Thunder with ice that falls from the sky": "Thunder + Hail",
    "BIIIIGGG Thunder with BIGG ice that falls from the sky": "Severe T-Storm",
    "Clear": "Clear",
    "Mostly Clear": "Mostly Clear",
    "Partly Cloudy": "Partly Cloudy",
    "Overcast": "Overcast",
    "Fog": "Fog",
    "Dense Fog": "Dense Fog",
    "Light Drizzle": "Drizzle",
    "Drizzle": "Drizzle",
    "Heavy Drizzle": "Heavy Drizzle",
    "Freezing Drizzle": "Frz Drizzle",
    "Heavy Freezing Drizzle": "Frz Drizzle",
    "Light Rain": "Light Rain",
    "Rain": "Rain",
    "Heavy Rain": "Heavy Rain",
    "Freezing Rain": "Frz Rain",
    "Heavy Freezing Rain": "Frz Rain",
    "Light Snow": "Light Snow",
    "Snow": "Snow",
    "Heavy Snow": "Heavy Snow",
    "Snow Grains": "Snow",
    "Rain Showers": "Showers",
    "Heavy Rain Showers": "Heavy Showers",
    "Violent Rain Showers": "Violent Rain",
    "Snow Showers": "Snow Showers",
    "Heavy Snow Showers": "Heavy Snow",
    "Thunderstorm": "Thunderstorm",
    "Thunderstorm with Hail": "T-Storm Hail",
    "Severe Thunderstorm with Hail": "Severe T-Storm",
}


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()

        ensure_directories()
        self.settings = load_settings()
        self.weather_api = WeatherAPI()

        self.weather_thread: QThread | None = None
        self.weather_worker: WeatherWorker | None = None

        self.current_location_query = ""
        self.current_weather_data: dict | None = None
        self.current_location_for_clock = "Local Forecast"
        self.current_utc_offset_seconds: int | None = None
        self.current_timezone_abbr = ""
        self.current_weather_code: int | None = None
        self.current_is_day = True

        self.ticker_message = " Enter a location to load your local weather ticker... "
        self.last_local_on_the_8s_key = ""
        self.city_index = self._load_city_index()

        self.setWindowTitle("The Weather Channel by Gary")
        self.resize(1400, 850)
        self.setMinimumSize(1100, 700)

        self.central = QWidget()
        self.central.setObjectName("RootWidget")
        self.setCentralWidget(self.central)

        self.root_layout = QVBoxLayout(self.central)
        self.root_layout.setContentsMargins(10, 10, 10, 10)
        self.root_layout.setSpacing(10)

        self.search_bar = SearchBar()
        self.spinner = LoadingSpinner()
        self.home_view = HomeView()

        self.control_row = QWidget()
        self.control_layout = QHBoxLayout(self.control_row)
        self.control_layout.setContentsMargins(0, 0, 0, 0)
        self.control_layout.setSpacing(8)

        self.search_button = QPushButton("Search")
        self.save_home_button = QPushButton("Set Home")
        self.refresh_button = QPushButton("Refresh")
        self.music_button = QPushButton("Music: On")
        self.view_button = QPushButton("View: Modern")
        self.settings_button = QPushButton("Settings")

        self.control_layout.addWidget(self.search_button)
        self.control_layout.addWidget(self.save_home_button)
        self.control_layout.addWidget(self.refresh_button)
        self.control_layout.addWidget(self.music_button)
        self.control_layout.addWidget(self.view_button)
        self.control_layout.addWidget(self.settings_button)
        self.control_layout.addStretch()

        self.root_layout.addWidget(self.search_bar)
        self.root_layout.addWidget(self.control_row)
        self.root_layout.addWidget(self.spinner)
        self.root_layout.addWidget(self.home_view, 1)

        self.spinner.hide()

        self.audio_output = QAudioOutput()
        self.player = QMediaPlayer()
        self.player.setAudioOutput(self.audio_output)
        self.player.mediaStatusChanged.connect(self._on_media_status_changed)

        if MUSIC_FILE.exists():
            self.player.setSource(QUrl.fromLocalFile(str(MUSIC_FILE)))

        self.search_bar.search_submitted.connect(self.handle_search)
        self.search_bar.location_selected.connect(self.handle_location_selected)
        self.search_button.clicked.connect(lambda: self.handle_search(self.search_bar.search_input.text()))
        self.save_home_button.clicked.connect(self.save_home_location)
        self.refresh_button.clicked.connect(self.refresh_current_location)
        self.music_button.clicked.connect(self.toggle_music)
        self.view_button.clicked.connect(self.toggle_view_mode)
        self.settings_button.clicked.connect(self.open_settings_dialog)

        self.clock_timer = QTimer(self)
        self.clock_timer.timeout.connect(self.update_clock)
        self.clock_timer.start(1000)

        self.ticker_timer = QTimer(self)
        self.ticker_timer.timeout.connect(self.scroll_ticker)
        self.refresh_ticker_timer_speed()
        self.ticker_timer.start()

        self.local_on_the_8s_timer = QTimer(self)
        self.local_on_the_8s_timer.timeout.connect(self.check_local_on_the_8s_refresh)
        self.local_on_the_8s_timer.start(30000)

        self.apply_view_mode()
        self.apply_music_settings()
        self.home_view.set_radar_visible(bool(self.settings.get("radar_enabled", True)))

        home_location = str(self.settings.get("home_location", "")).strip()
        if home_location:
            self.search_bar.search_input.setText(home_location)
            QTimer.singleShot(500, lambda: self.handle_search(home_location))

        self.update_clock()

    def _load_city_index(self) -> list[dict]:
        if not CITIES_JSON.exists():
            return []

        try:
            with CITIES_JSON.open("r", encoding="utf-8") as file:
                data = json.load(file)
            if isinstance(data, list):
                return [item for item in data if isinstance(item, dict)]
        except Exception:
            pass

        return []

    def apply_view_mode(self) -> None:
        mode = self.settings.get("ui_mode", "modern")
        self.setStyleSheet(build_stylesheet(mode))
        self.home_view.set_view_mode(mode)
        self.view_button.setText(f"View: {mode.title()}")

        if DEFAULT_BG_FILE.exists():
            self._apply_background_file(DEFAULT_BG_FILE)

    def _apply_background_file(self, image_path) -> None:
        path = str(image_path).replace("\\", "/")
        self.central.setStyleSheet(
            f"""
            QWidget#RootWidget {{
                background-image: url("{path}");
                background-position: center;
                background-repeat: no-repeat;
            }}
            """
        )

    def _apply_background(self, filename: str) -> None:
        image_path = BACKGROUNDS_DIR / filename
        if image_path.exists():
            self._apply_background_file(image_path)
        elif DEFAULT_BG_FILE.exists():
            self._apply_background_file(DEFAULT_BG_FILE)

    def apply_music_settings(self) -> None:
        volume = int(self.settings.get("music_volume", 35))
        self.audio_output.setVolume(max(0.0, min(1.0, volume / 100.0)))

        enabled = bool(self.settings.get("music_enabled", True))
        self.music_button.setText(f"Music: {'On' if enabled else 'Off'}")

        if enabled and MUSIC_FILE.exists():
            self.player.play()
        else:
            self.player.stop()

    def _on_media_status_changed(self, status) -> None:
        if status == QMediaPlayer.MediaStatus.EndOfMedia and bool(
            self.settings.get("music_enabled", True)
        ):
            self.player.setPosition(0)
            self.player.play()

    def toggle_music(self) -> None:
        self.settings["music_enabled"] = not bool(self.settings.get("music_enabled", True))
        save_settings(self.settings)
        self.apply_music_settings()

    def toggle_view_mode(self) -> None:
        current = self.settings.get("ui_mode", "modern")
        self.settings["ui_mode"] = "classic" if current == "modern" else "modern"
        save_settings(self.settings)
        self.apply_view_mode()

        if self.current_weather_data:
            self.update_from_loaded_data(self.current_weather_data)

    def open_settings_dialog(self) -> None:
        dialog = SettingsDialog(self.settings, self)
        if dialog.exec():
            updated = dialog.get_settings()
            self.settings.update(updated)
            save_settings(self.settings)

            self.apply_view_mode()
            self.apply_music_settings()
            self.home_view.set_radar_visible(bool(self.settings.get("radar_enabled", True)))
            self.refresh_ticker_timer_speed()

            home_location = str(self.settings.get("home_location", "")).strip()
            if home_location:
                self.search_bar.search_input.setText(home_location)

            if self.current_weather_data:
                self.update_from_loaded_data(self.current_weather_data)

    def save_home_location(self) -> None:
        query = self.search_bar.search_input.text().strip()
        if not query:
            return

        self.settings["home_location"] = query
        save_settings(self.settings)

    def handle_search(self, query: str) -> None:
        query = query.strip()
        if not query:
            self.clear_weather_display()
            return

        self.current_location_query = query
        self.home_view.subtitle_label.setText(f"Loading weather for {query}...")
        self.home_view.clear_conditions("Loading weather...")
        self.home_view.set_classic_status("Loading weather...")
        self.spinner.start()

        self._cleanup_weather_thread()

        self.weather_thread = QThread()
        self.weather_worker = WeatherWorker(query)
        self.weather_worker.moveToThread(self.weather_thread)

        self.weather_thread.started.connect(self.weather_worker.run)
        self.weather_worker.finished.connect(self._on_weather_loaded)
        self.weather_worker.failed.connect(self._on_weather_failed)

        self.weather_worker.finished.connect(self.weather_thread.quit)
        self.weather_worker.failed.connect(self.weather_thread.quit)
        self.weather_thread.finished.connect(self._finalize_weather_thread)

        self.weather_thread.start()

    def handle_location_selected(self, location: dict) -> None:
        display_name = location.get("display_name", "") or location.get("city", "")
        if display_name:
            self.search_bar.search_input.setText(display_name)
            self.handle_search(display_name)

    def _on_weather_loaded(self, payload: dict) -> None:
        self.spinner.stop()
        self.current_weather_data = payload
        self.update_from_loaded_data(payload)

    def _on_weather_failed(self, message: str) -> None:
        self.spinner.stop()
        self.home_view.subtitle_label.setText(message)
        self.home_view.clear_conditions("Weather unavailable")
        self.home_view.set_classic_status("Weather load failed.")

        if DEFAULT_BG_FILE.exists():
            self._apply_background_file(DEFAULT_BG_FILE)

    def update_from_loaded_data(self, data: dict) -> None:
        location_info = data.get("location", {})
        current = data.get("current", {})
        daily = data.get("daily", {})
        hourly = data.get("hourly", {})
        air_quality = data.get("air_quality", {})
        alerts = data.get("alerts", [])

        place_name = location_info.get("name", "Unknown")
        state = location_info.get("state", "")
        country = location_info.get("country", "")
        latitude = location_info.get("latitude")
        longitude = location_info.get("longitude")

        display_location = f"{place_name}, {state}" if state else f"{place_name}, {country}"

        self.current_location_for_clock = display_location
        self.current_utc_offset_seconds = data.get("utc_offset_seconds", None)
        self.current_timezone_abbr = data.get("timezone_abbreviation", "") or ""

        weather_code = current.get("weather_code", -1)
        is_day = current.get("is_day", 1)

        self.current_weather_code = int(weather_code) if isinstance(weather_code, (int, float)) else -1
        self.current_is_day = bool(is_day)

        temp = current.get("temperature_2m")
        feels_like = current.get("apparent_temperature")
        humidity = current.get("relative_humidity_2m")
        wind = current.get("wind_speed_10m")

        icon_filename = self.weather_code_to_icon_filename(self.current_weather_code, self.current_is_day)
        condition_text = self.get_condition_text(self.current_weather_code)
        aqi_value = air_quality.get("us_aqi")
        aqi_text = self.weather_api.aqi_to_text(aqi_value)

        self.home_view.subtitle_label.setText(display_location)
        self.home_view.update_weather_card(
            location_name=display_location,
            temperature=f"{round(temp)}°F" if isinstance(temp, (int, float)) else "--°F",
            condition_text=condition_text,
            feels_like_text=(
                f"Feels Like: {round(feels_like)}°F" if isinstance(feels_like, (int, float)) else "Feels Like: --°F"
            ),
            humidity_text=(
                f"Humidity: {round(humidity)}%" if isinstance(humidity, (int, float)) else "Humidity: --%"
            ),
            wind_text=(
                f"Wind: {round(wind)} mph" if isinstance(wind, (int, float)) else "Wind: -- mph"
            ),
            aqi_text=(
                f"Air Quality: {round(aqi_value)} ({aqi_text})" if isinstance(aqi_value, (int, float)) else "Air Quality: --"
            ),
            icon_filename=icon_filename,
            updated_text="Current conditions",
        )

        self.home_view.set_alerts(alerts)
        self.home_view.set_classic_status("Weather loaded.")
        self.home_view.set_classic_report(
            self.build_classic_text_report(
                display_location=display_location,
                query=self.current_location_query,
                current=current,
                daily=daily,
                hourly=hourly,
                air_quality=air_quality,
                alerts=alerts,
            )
        )

        self.update_forecast_panel(daily)
        self.update_hourly_panel(hourly)

        if isinstance(latitude, (int, float)) and isinstance(longitude, (int, float)):
            self.home_view.set_radar_location(float(latitude), float(longitude))
            self.update_local_ticker(float(latitude), float(longitude))

        self.update_clock()
        self._apply_background(self.background_for_weather(self.current_weather_code, self.current_is_day))

    def update_clock(self) -> None:
        try:
            if isinstance(self.current_utc_offset_seconds, int):
                utc_now = datetime.now(timezone.utc)
                local_time = utc_now + timedelta(seconds=self.current_utc_offset_seconds)
            else:
                local_time = datetime.now()

            time_text = local_time.strftime("%A %I:%M:%S %p").replace(" 0", " ")
            if self.current_timezone_abbr:
                time_text = f"{time_text} {self.current_timezone_abbr}"

            self.setWindowTitle(f"The Weather Channel by Gary - {self.current_location_for_clock} - {time_text}")
        except Exception:
            pass

    def refresh_ticker_timer_speed(self) -> None:
        speed = int(self.settings.get("ticker_speed_ms", 120))
        self.ticker_timer.setInterval(max(40, speed))

    def scroll_ticker(self) -> None:
        if self.ticker_message:
            self.ticker_message = self.ticker_message[1:] + self.ticker_message[0]
            self.home_view.set_ticker_text(self.ticker_message)

    def check_local_on_the_8s_refresh(self) -> None:
        if not self.current_location_query:
            return

        now_for_weather = datetime.now()

        if isinstance(self.current_utc_offset_seconds, int):
            utc_now = datetime.now(timezone.utc)
            now_for_weather = (
                utc_now + timedelta(seconds=self.current_utc_offset_seconds)
            ).replace(tzinfo=None)

        minute = now_for_weather.minute
        second = now_for_weather.second

        if minute % 8 == 0 and second < 30:
            refresh_key = f"{self.current_location_query}-{now_for_weather.strftime('%Y%m%d%H%M')}"
            if refresh_key == self.last_local_on_the_8s_key:
                return

            self.last_local_on_the_8s_key = refresh_key
            self.home_view.set_classic_status("*** LOCAL ON THE 8s UPDATE ***")
            self.handle_search(self.current_location_query)

    def distance(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        return (lat1 - lat2) ** 2 + (lon1 - lon2) ** 2

    def get_nearby_cities(self, latitude: float, longitude: float, count: int = 5) -> list[tuple[str, float, float]]:
        city_distances = []

        for city in self.city_index:
            city_name = city.get("city", "")
            state = city.get("state", "")
            lat = city.get("lat")
            lon = city.get("lon")

            if not city_name or not isinstance(lat, (int, float)) or not isinstance(lon, (int, float)):
                continue

            display = f"{city_name}, {state}" if state else city_name
            city_distances.append(
                (self.distance(latitude, longitude, float(lat), float(lon)), display, float(lat), float(lon))
            )

        city_distances.sort(key=lambda item: item[0])
        return [(name, lat, lon) for _, name, lat, lon in city_distances[:count]]

    def update_local_ticker(self, latitude: float, longitude: float) -> None:
        if not self.city_index:
            self.ticker_message = f" {self.current_location_for_clock}: Weather loaded... "
            self.home_view.set_ticker_text(self.ticker_message)
            return

        try:
            ticker_parts = []
            nearby_cities = self.get_nearby_cities(latitude, longitude, 5)

            for city_name, _, _ in nearby_cities:
                try:
                    weather = self.weather_api.get_weather(city_name)
                    current = weather.get("current", {})
                    temp = current.get("temperature_2m")
                    code = current.get("weather_code", -1)

                    condition = self.legacy_short_condition_text(self.get_condition_text(code))
                    temp_text = f"{round(temp)}°F" if isinstance(temp, (int, float)) else "--°F"
                    ticker_parts.append(f"{city_name}: {temp_text}, {condition}")
                except Exception:
                    ticker_parts.append(f"{city_name}: IDK Weather")

            self.ticker_message = "   ***   ".join(ticker_parts) + "   ***   "
            self.home_view.set_ticker_text(self.ticker_message)
        except Exception:
            pass

    def get_condition_text(self, weather_code: int) -> str:
        mode = self.settings.get("description_mode", "funny")
        if mode == "normal":
            return NORMAL_WEATHER_CODES.get(weather_code, "Unknown")
        return FUNNY_WEATHER_CODES.get(weather_code, "Unknown")

    def legacy_short_condition_text(self, text: str) -> str:
        return SHORT_TEXT.get(text, text)

    def weather_code_to_icon_filename(self, code: int, is_day: bool = True) -> str:
        is_day = bool(is_day)

        code_map = {
            0: "clear_day.png" if is_day else "clear_night.png",
            1: "mostly_clear_day.png" if is_day else "mostly_clear_night.png",
            2: "partly_cloudy_day.png" if is_day else "partly_cloudy_night.png",
            3: "overcast.png",
            45: "fog.png",
            48: "fog_heavy.png",
            51: "drizzle_light.png",
            53: "drizzle.png",
            55: "drizzle_heavy.png",
            56: "freezing_rain_light.png",
            57: "freezing_rain_heavy.png",
            61: "rain.png",
            63: "rain.png",
            65: "rain_heavy.png",
            66: "freezing_rain.png",
            67: "freezing_rain_heavy.png",
            71: "snow_light.png",
            73: "snow.png",
            75: "snow_heavy.png",
            77: "flurries.png",
            80: "showers.png",
            81: "showers_heavy.png",
            82: "downpour.png",
            85: "snow_showers_light.png",
            86: "snow_showers_heavy.png",
            95: "thunderstorm.png",
            96: "thunderstorm_hail.png",
            99: "thunderstorm_heavy.png",
        }
        return code_map.get(code, "cloudy.png")

    def background_for_weather(self, code: int | None, is_day: bool) -> str:
        if code is None:
            return "clear_day.jpg" if is_day else "clear_night.jpg"

        if code in {95, 96, 99}:
            return "storm.jpg"
        if code in {71, 73, 75, 77, 85, 86}:
            return "snow.jpg"
        if code in {45, 48}:
            return "fog.jpg"
        if code in {51, 53, 55, 56, 57, 61, 63, 65, 66, 67, 80, 81, 82}:
            return "rain.jpg"
        if code == 3:
            return "cloudy.jpg"
        if code in {1, 2}:
            return "partly_cloudy.jpg"
        return "clear_day.jpg" if is_day else "clear_night.jpg"

    def build_classic_text_report(
        self,
        display_location: str,
        query: str,
        current: dict,
        daily: dict,
        hourly: dict,
        air_quality: dict,
        alerts: list[dict],
    ) -> str:
        lines: list[str] = []
        updated_time = datetime.now().strftime("%m/%d/%Y  %I:%M %p")

        temp = current.get("temperature_2m")
        feels_like = current.get("apparent_temperature")
        humidity = current.get("relative_humidity_2m")
        wind = current.get("wind_speed_10m")
        weather_code = current.get("weather_code", -1)

        legacy_condition = self.get_condition_text(weather_code)
        us_aqi = air_quality.get("us_aqi")
        aqi_text = self.weather_api.aqi_to_text(us_aqi)

        lines.append("==============================")
        lines.append("      LOCAL ON THE 8s         ")
        lines.append("==============================")
        lines.append("")
        lines.append(" CURRENT CONDITIONS")
        lines.append(" ------------------")
        lines.append(f" Location: {display_location}")
        lines.append(f" Search:   {query}")
        lines.append(f" Updated:  {updated_time}")
        lines.append("")
        lines.append(f" Weather:  {legacy_condition}")
        lines.append(f" Temp:     {round(temp)}°F" if isinstance(temp, (int, float)) else " Temp:     --°F")
        lines.append(
            f" Feels:    {round(feels_like)}°F"
            if isinstance(feels_like, (int, float)) else
            " Feels:    --°F"
        )
        lines.append(
            f" Humid:    {round(humidity)}%"
            if isinstance(humidity, (int, float)) else
            " Humid:    --%"
        )
        lines.append(
            f" Wind:     {round(wind)} mph"
            if isinstance(wind, (int, float)) else
            " Wind:     -- mph"
        )
        lines.append("")
        lines.append(" AIR QUALITY")
        lines.append(" -----------")
        if isinstance(us_aqi, (int, float)):
            lines.append(f" AQI:      {round(us_aqi)}")
            lines.append(f" Status:   {aqi_text}")
        else:
            lines.append(" AQI:      --")
            lines.append(" Status:   Unknown")

        lines.append("")
        lines.append(" ALERTS")
        lines.append(" ------")
        if alerts:
            for alert in alerts[:3]:
                lines.append(f" {alert.get('event', 'Alert')} [{alert.get('severity', 'Unknown')}]")
        else:
            lines.append(" No active alerts")

        lines.append("")
        lines.append(" 5-DAY FORECAST")
        lines.append(" --------------")

        dates = daily.get("time", [])
        weather_codes = daily.get("weather_code", [])
        max_temps = daily.get("temperature_2m_max", [])
        min_temps = daily.get("temperature_2m_min", [])

        for i in range(min(5, len(dates))):
            try:
                date_obj = datetime.strptime(dates[i], "%Y-%m-%d")
                day_name = date_obj.strftime("%a")
            except ValueError:
                day_name = "Day"

            d_code = weather_codes[i] if i < len(weather_codes) else -1
            d_cond = self.legacy_short_condition_text(self.get_condition_text(d_code))

            d_max = max_temps[i] if i < len(max_temps) else None
            d_min = min_temps[i] if i < len(min_temps) else None

            high_text = f"{round(d_max)}°" if isinstance(d_max, (int, float)) else "--°"
            low_text = f"{round(d_min)}°" if isinstance(d_min, (int, float)) else "--°"

            lines.append(f" {day_name:<4} {high_text:>4} / {low_text:<4}  {d_cond}")

        lines.append("")
        lines.append(" 12-HOUR FORECAST")
        lines.append(" ----------------")

        times = hourly.get("time", [])
        temps = hourly.get("temperature_2m", [])
        hour_codes = hourly.get("weather_code", [])
        rain_probs = hourly.get("precipitation_probability", [])
        wind_speeds = hourly.get("wind_speed_10m", [])

        start_index = 0
        now_for_weather = datetime.now()

        if isinstance(self.current_utc_offset_seconds, int):
            utc_now = datetime.now(timezone.utc)
            now_for_weather = (
                utc_now + timedelta(seconds=self.current_utc_offset_seconds)
            ).replace(tzinfo=None)

        current_hour = now_for_weather.replace(minute=0, second=0, microsecond=0)

        for i, time_str in enumerate(times):
            try:
                hour_time = datetime.fromisoformat(time_str)
                if hour_time >= current_hour:
                    start_index = i
                    break
            except ValueError:
                continue

        for i in range(12):
            idx = start_index + i
            if idx >= len(times):
                break

            try:
                hour_time = datetime.fromisoformat(times[idx])
                time_text = hour_time.strftime("%I %p").lstrip("0")
            except ValueError:
                time_text = "---"

            h_temp = temps[idx] if idx < len(temps) else None
            h_code = hour_codes[idx] if idx < len(hour_codes) else -1
            h_rain = rain_probs[idx] if idx < len(rain_probs) else None
            h_wind = wind_speeds[idx] if idx < len(wind_speeds) else None

            h_cond = self.legacy_short_condition_text(self.get_condition_text(h_code))

            temp_text = f"{round(h_temp)}°F" if isinstance(h_temp, (int, float)) else "--°F"
            rain_text = f"{round(h_rain)}%" if isinstance(h_rain, (int, float)) else "--%"
            wind_text = f"{round(h_wind)} mph" if isinstance(h_wind, (int, float)) else "--"

            lines.append(f" {time_text:<5} {temp_text:>5}  Rain {rain_text:>3}  Wind {wind_text:>7}  {h_cond}")

        lines.append("")
        lines.append(" Thanks for using my weather app!")
        lines.append("")
        lines.append("==============================")

        return "\n".join(lines)

    def update_forecast_panel(self, daily_data: dict) -> None:
        dates = daily_data.get("time", [])
        weather_codes = daily_data.get("weather_code", [])
        max_temps = daily_data.get("temperature_2m_max", [])
        min_temps = daily_data.get("temperature_2m_min", [])

        rows: list[dict] = []

        for i in range(5):
            if i < len(dates):
                try:
                    date_obj = datetime.strptime(dates[i], "%Y-%m-%d")
                    day_name = date_obj.strftime("%a")
                except ValueError:
                    day_name = "Day"

                weather_code = weather_codes[i] if i < len(weather_codes) else -1
                condition = self.weather_api.weather_code_to_text(weather_code)

                max_temp = max_temps[i] if i < len(max_temps) else None
                min_temp = min_temps[i] if i < len(min_temps) else None

                temp_text = (
                    f"{round(max_temp)}° / {round(min_temp)}°"
                    if isinstance(max_temp, (int, float)) and isinstance(min_temp, (int, float))
                    else "--° / --°"
                )

                rows.append(
                    {
                        "day": day_name,
                        "condition": condition,
                        "temp": temp_text,
                        "icon": self.weather_code_to_icon_filename(weather_code, True),
                    }
                )
            else:
                rows.append(
                    {
                        "day": "---",
                        "condition": "No data",
                        "temp": "--° / --°",
                        "icon": "cloudy.png",
                    }
                )

        self.home_view.update_forecast_rows(rows)

    def update_hourly_panel(self, hourly_data: dict) -> None:
        times = hourly_data.get("time", [])
        temps = hourly_data.get("temperature_2m", [])
        weather_codes = hourly_data.get("weather_code", [])

        start_index = 0
        now_for_weather = datetime.now()

        if isinstance(self.current_utc_offset_seconds, int):
            utc_now = datetime.now(timezone.utc)
            now_for_weather = (
                utc_now + timedelta(seconds=self.current_utc_offset_seconds)
            ).replace(tzinfo=None)

        current_hour = now_for_weather.replace(minute=0, second=0, microsecond=0)

        for i, time_str in enumerate(times):
            try:
                hour_time = datetime.fromisoformat(time_str)
                if hour_time >= current_hour:
                    start_index = i
                    break
            except ValueError:
                continue

        rows: list[dict] = []

        for row_index in range(24):
            data_index = start_index + row_index

            if data_index < len(times):
                try:
                    hour_time = datetime.fromisoformat(times[data_index])
                    time_text = hour_time.strftime("%I %p").lstrip("0")
                    is_day = 6 <= hour_time.hour < 18
                except ValueError:
                    time_text = "---"
                    is_day = True

                temp = temps[data_index] if data_index < len(temps) else None
                weather_code = weather_codes[data_index] if data_index < len(weather_codes) else -1
                condition = self.weather_api.weather_code_to_text(weather_code)

                rows.append(
                    {
                        "time": time_text,
                        "condition": condition,
                        "temp": f"{round(temp)}°" if isinstance(temp, (int, float)) else "--°",
                        "icon": self.weather_code_to_icon_filename(weather_code, is_day),
                    }
                )
            else:
                rows.append(
                    {
                        "time": "---",
                        "condition": "No data",
                        "temp": "--°",
                        "icon": "cloudy.png",
                    }
                )

        self.home_view.update_hourly_rows(rows)

    def refresh_current_location(self) -> None:
        if self.current_location_query:
            self.handle_search(self.current_location_query)
        else:
            query = self.search_bar.search_input.text().strip()
            if query:
                self.handle_search(query)
            else:
                QMessageBox.information(self, "Refresh", "Search for a location first.")

    def clear_weather_display(self) -> None:
        self.current_weather_data = None
        self.current_weather_code = None
        self.current_is_day = True
        self.current_location_for_clock = "Local Forecast"
        self.current_utc_offset_seconds = None
        self.current_timezone_abbr = ""

        self.home_view.subtitle_label.setText("Search for a city, state, or ZIP to begin.")
        self.home_view.clear_conditions("Please enter a location")
        self.home_view.set_classic_status("Ready.")
        self.home_view.set_classic_report("Awaiting location input...")
        self.update_clock()

        if DEFAULT_BG_FILE.exists():
            self._apply_background_file(DEFAULT_BG_FILE)

    def _finalize_weather_thread(self) -> None:
        if self.weather_worker is not None:
            try:
                self.weather_worker.deleteLater()
            except Exception:
                pass
            self.weather_worker = None

        if self.weather_thread is not None:
            try:
                self.weather_thread.deleteLater()
            except Exception:
                pass
            self.weather_thread = None

    def _cleanup_weather_thread(self) -> None:
        if self.weather_thread is None:
            return

        thread = self.weather_thread

        if thread.isRunning():
            try:
                thread.requestInterruption()
            except Exception:
                pass

            try:
                thread.quit()
            except Exception:
                pass

            if not thread.wait(3000):
                try:
                    thread.terminate()
                except Exception:
                    pass
                thread.wait(2000)

        self._finalize_weather_thread()

    def closeEvent(self, event: QCloseEvent) -> None:
        self.player.stop()
        self.spinner.stop()
        self._cleanup_weather_thread()
        event.accept()