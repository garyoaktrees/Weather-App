from __future__ import annotations

import requests


class WeatherAPI:
    def __init__(self) -> None:
        self.geocode_url = "https://geocoding-api.open-meteo.com/v1/search"
        self.forecast_url = "https://api.open-meteo.com/v1/forecast"
        self.air_quality_url = "https://air-quality-api.open-meteo.com/v1/air-quality"
        self.zip_url = "https://api.zippopotam.us/us"

        self.nws_points_url = "https://api.weather.gov/points"
        self.nws_alerts_url = "https://api.weather.gov/alerts/active/zone"

        self.default_headers = {
            "User-Agent": "GaryWeatherApp/2.0 (desktop weather app)",
            "Accept": "application/geo+json, application/json",
        }

        self.state_name_to_code = {
            "alabama": "AL", "alaska": "AK", "arizona": "AZ", "arkansas": "AR",
            "california": "CA", "colorado": "CO", "connecticut": "CT", "delaware": "DE",
            "district of columbia": "DC", "florida": "FL", "georgia": "GA",
            "hawaii": "HI", "idaho": "ID", "illinois": "IL", "indiana": "IN",
            "iowa": "IA", "kansas": "KS", "kentucky": "KY", "louisiana": "LA",
            "maine": "ME", "maryland": "MD", "massachusetts": "MA", "michigan": "MI",
            "minnesota": "MN", "mississippi": "MS", "missouri": "MO", "montana": "MT",
            "nebraska": "NE", "nevada": "NV", "new hampshire": "NH", "new jersey": "NJ",
            "new mexico": "NM", "new york": "NY", "north carolina": "NC",
            "north dakota": "ND", "ohio": "OH", "oklahoma": "OK", "oregon": "OR",
            "pennsylvania": "PA", "rhode island": "RI", "south carolina": "SC",
            "south dakota": "SD", "tennessee": "TN", "texas": "TX", "utah": "UT",
            "vermont": "VT", "virginia": "VA", "washington": "WA",
            "west virginia": "WV", "wisconsin": "WI", "wyoming": "WY",
        }

        self.state_code_to_name = {v: k.title() for k, v in self.state_name_to_code.items()}

        self.session = requests.Session()
        self.session.headers.update(self.default_headers)

        self.location_cache: dict[str, dict] = {}
        self.weather_cache: dict[str, dict] = {}

    def normalize_state_code(self, value: str) -> str:
        if not value:
            return ""

        value = value.strip()
        if len(value) == 2 and value.isalpha():
            return value.upper()

        return self.state_name_to_code.get(value.lower(), "")

    def state_matches(self, result: dict, requested_state_code: str) -> bool:
        if not requested_state_code:
            return True

        fields_to_check = [
            str(result.get("admin1", "")).strip(),
            str(result.get("admin2", "")).strip(),
            str(result.get("state", "")).strip(),
        ]

        requested_state_name = self.state_code_to_name.get(requested_state_code, "").lower()

        for field in fields_to_check:
            if not field:
                continue

            if self.normalize_state_code(field) == requested_state_code:
                return True

            if field.lower() == requested_state_name:
                return True

        return False

    def looks_like_zip(self, location: str) -> bool:
        return location.isdigit() and len(location) == 5

    def clean_location_input(self, location: str) -> str:
        return " ".join(location.strip().split())

    def parse_city_state_input(self, location: str) -> tuple[str, str]:
        parts = [p.strip() for p in location.split(",") if p.strip()]

        if len(parts) >= 2:
            city_part = parts[0]
            state_part = self.normalize_state_code(parts[1])
            return city_part, state_part

        return location.strip(), ""

    def request_json(self, url: str, *, params=None, timeout: int = 8, headers=None) -> dict:
        response = self.session.get(url, params=params, timeout=timeout, headers=headers)
        response.raise_for_status()
        return response.json()

    def get_location_data_from_zip(self, zip_code: str) -> dict:
        data = self.request_json(f"{self.zip_url}/{zip_code}", timeout=6)

        places = data.get("places", [])
        if not places:
            raise ValueError("ZIP code not found.")

        place = places[0]

        return {
            "name": place.get("place name", "Unknown"),
            "admin1": place.get("state abbreviation", place.get("state", "")),
            "country": data.get("country", "United States"),
            "latitude": float(place["latitude"]),
            "longitude": float(place["longitude"]),
        }

    def score_result(self, result: dict, raw_query: str = "") -> int:
        score = 0

        name = str(result.get("name", "")).strip().lower()
        raw_query = raw_query.lower().strip()

        if name == raw_query:
            score += 100
        elif raw_query and raw_query in name:
            score += 40

        if str(result.get("country_code", "")).upper() == "US":
            score += 20

        population = result.get("population")
        if isinstance(population, int):
            score += min(population // 50000, 25)

        latitude = result.get("latitude")
        longitude = result.get("longitude")
        if isinstance(latitude, (int, float)) and isinstance(longitude, (int, float)):
            score += 5

        return score

    def search_geocoder(self, query: str) -> list[dict]:
        params = {
            "name": query,
            "count": 20,
            "language": "en",
            "format": "json",
            "countryCode": "US",
        }
        data = self.request_json(self.geocode_url, params=params, timeout=8)
        return data.get("results") or []

    def get_location_data_from_geocoder(self, location: str) -> dict:
        location = self.clean_location_input(location)
        city_part, requested_state_code = self.parse_city_state_input(location)

        queries: list[str] = []
        if requested_state_code:
            queries.append(location)
        queries.append(city_part)

        seen = set()
        all_results: list[dict] = []

        for query in queries:
            key = query.lower()
            if key in seen:
                continue
            seen.add(key)
            all_results.extend(self.search_geocoder(query))

        if not all_results:
            raise ValueError("Location not found. Try city, state or a ZIP code.")

        if requested_state_code:
            filtered_results = [r for r in all_results if self.state_matches(r, requested_state_code)]
            if not filtered_results:
                raise ValueError(f"No matching city found in {requested_state_code}.")
            all_results = filtered_results

        best_result = max(all_results, key=lambda r: self.score_result(r, raw_query=city_part))

        return {
            "name": best_result.get("name", "Unknown"),
            "admin1": best_result.get("admin1", ""),
            "country": best_result.get("country", "United States"),
            "latitude": best_result.get("latitude"),
            "longitude": best_result.get("longitude"),
        }

    def get_location_data(self, location: str) -> dict:
        location = self.clean_location_input(location)

        if not location:
            raise ValueError("Please enter a ZIP code, city, or city and state.")

        cache_key = location.lower()
        if cache_key in self.location_cache:
            return self.location_cache[cache_key]

        if self.looks_like_zip(location):
            result = self.get_location_data_from_zip(location)
        else:
            result = self.get_location_data_from_geocoder(location)

        self.location_cache[cache_key] = result
        return result

    def get_air_quality(self, latitude: float, longitude: float) -> dict:
        params = {
            "latitude": latitude,
            "longitude": longitude,
            "current": ["us_aqi"],
            "timezone": "auto",
        }

        data = self.request_json(self.air_quality_url, params=params, timeout=6)
        return data.get("current", {})

    def get_alerts(self, latitude: float, longitude: float) -> list[dict]:
        try:
            points_data = self.request_json(
                f"{self.nws_points_url}/{latitude},{longitude}",
                timeout=6,
                headers=self.default_headers,
            )

            zone_url = points_data.get("properties", {}).get("forecastZone", "")
            if not zone_url:
                return []

            zone = zone_url.rstrip("/").split("/")[-1]

            alerts_data = self.request_json(
                f"{self.nws_alerts_url}/{zone}",
                timeout=6,
                headers=self.default_headers,
            )

            alerts: list[dict] = []

            for feature in alerts_data.get("features", []):
                props = feature.get("properties", {}) or {}
                alerts.append(
                    {
                        "headline": props.get("headline") or props.get("event") or "Weather Alert",
                        "event": props.get("event", "Weather Alert"),
                        "severity": props.get("severity", "Unknown"),
                        "urgency": props.get("urgency", ""),
                        "certainty": props.get("certainty", ""),
                        "description": props.get("description", ""),
                        "instruction": props.get("instruction", ""),
                    }
                )

            return alerts

        except Exception:
            return []

    def get_weather(self, location: str) -> dict:
        location = self.clean_location_input(location)
        cache_key = location.lower()

        if cache_key in self.weather_cache:
            return self.weather_cache[cache_key]

        location_data = self.get_location_data(location)

        weather_params = {
            "latitude": location_data["latitude"],
            "longitude": location_data["longitude"],
            "current": [
                "temperature_2m",
                "apparent_temperature",
                "relative_humidity_2m",
                "is_day",
                "precipitation",
                "weather_code",
                "wind_speed_10m",
            ],
            "hourly": [
                "temperature_2m",
                "precipitation_probability",
                "weather_code",
                "wind_speed_10m",
            ],
            "daily": [
                "weather_code",
                "temperature_2m_max",
                "temperature_2m_min",
                "precipitation_probability_max",
            ],
            "temperature_unit": "fahrenheit",
            "wind_speed_unit": "mph",
            "precipitation_unit": "inch",
            "timezone": "auto",
            "forecast_days": 5,
        }

        weather_data = self.request_json(self.forecast_url, params=weather_params, timeout=8)

        try:
            air_quality = self.get_air_quality(
                location_data["latitude"],
                location_data["longitude"],
            )
        except Exception:
            air_quality = {}

        try:
            alerts = self.get_alerts(
                location_data["latitude"],
                location_data["longitude"],
            )
        except Exception:
            alerts = []

        result = {
            "location": {
                "name": location_data.get("name", "Unknown"),
                "state": location_data.get("admin1", ""),
                "country": location_data.get("country", ""),
                "latitude": location_data.get("latitude"),
                "longitude": location_data.get("longitude"),
            },
            "timezone": weather_data.get("timezone", ""),
            "timezone_abbreviation": weather_data.get("timezone_abbreviation", ""),
            "utc_offset_seconds": weather_data.get("utc_offset_seconds", 0),
            "current": weather_data.get("current", {}),
            "hourly": weather_data.get("hourly", {}),
            "daily": weather_data.get("daily", {}),
            "air_quality": air_quality,
            "alerts": alerts,
        }

        self.weather_cache[cache_key] = result
        return result

    @staticmethod
    def weather_code_to_text(code: int) -> str:
        code_map = {
            0: "Clear sky",
            1: "Mostly clear",
            2: "Partly cloudy",
            3: "Overcast",
            45: "Fog",
            48: "Depositing rime fog",
            51: "Light drizzle",
            53: "Moderate drizzle",
            55: "Dense drizzle",
            56: "Freezing drizzle",
            57: "Heavy freezing drizzle",
            61: "Slight rain",
            63: "Moderate rain",
            65: "Heavy rain",
            66: "Freezing rain",
            67: "Heavy freezing rain",
            71: "Slight snow",
            73: "Moderate snow",
            75: "Heavy snow",
            77: "Snow grains",
            80: "Slight rain showers",
            81: "Moderate rain showers",
            82: "Violent rain showers",
            85: "Snow showers",
            86: "Heavy snow showers",
            95: "Thunderstorm",
            96: "Thunderstorm with light hail",
            99: "Thunderstorm with heavy hail",
        }
        return code_map.get(code, "Unknown")

    @staticmethod
    def aqi_to_text(aqi) -> str:
        if not isinstance(aqi, (int, float)):
            return "Unknown"

        if aqi <= 50:
            return "Good"
        if aqi <= 100:
            return "Moderate"
        if aqi <= 150:
            return "Unhealthy for Sensitive Groups"
        if aqi <= 200:
            return "Unhealthy"
        if aqi <= 300:
            return "Very Unhealthy"

        return "Hazardous"

    def clear_cache(self) -> None:
        self.location_cache.clear()
        self.weather_cache.clear()