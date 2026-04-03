from __future__ import annotations

import json
from dataclasses import dataclass, asdict
from typing import Any

import requests

from app.core.config import MAX_AUTOCOMPLETE_RESULTS, MIN_SEARCH_CHARS
from app.core.paths import CITIES_JSON


@dataclass
class LocationResult:
    city: str
    state: str = ""
    state_name: str = ""
    lat: float = 0.0
    lon: float = 0.0
    zip: str = ""
    country: str = "United States"
    source: str = "local"

    @property
    def display_name(self) -> str:
        if self.state:
            return f"{self.city}, {self.state}"
        return self.city

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["display_name"] = self.display_name
        return data


class LocationService:
    def __init__(self) -> None:
        self._cities: list[LocationResult] = self._load_cities()

    def _load_cities(self) -> list[LocationResult]:
        if not CITIES_JSON.exists():
            return []

        try:
            with CITIES_JSON.open("r", encoding="utf-8") as file:
                raw = json.load(file)
        except Exception:
            return []

        cities: list[LocationResult] = []
        if not isinstance(raw, list):
            return cities

        for item in raw:
            if not isinstance(item, dict):
                continue

            cities.append(
                LocationResult(
                    city=str(item.get("city", "")).strip(),
                    state=str(item.get("state", "")).strip().upper(),
                    state_name=str(item.get("state_name", "")).strip(),
                    lat=float(item.get("lat", 0.0) or 0.0),
                    lon=float(item.get("lon", 0.0) or 0.0),
                    zip=str(item.get("zip", "")).strip(),
                    country=str(item.get("country", "United States")).strip(),
                    source="local",
                )
            )

        return cities

    def search_local(self, query: str, limit: int = MAX_AUTOCOMPLETE_RESULTS) -> list[LocationResult]:
        query = query.strip()
        if len(query) < MIN_SEARCH_CHARS:
            return []

        normalized = query.lower()
        compact = normalized.replace(",", " ")
        parts = [p for p in compact.split() if p]

        startswith_matches: list[LocationResult] = []
        contains_matches: list[LocationResult] = []

        for city in self._cities:
            city_name = city.city.lower()
            state_code = city.state.lower()
            state_name = city.state_name.lower()
            zip_code = city.zip.lower()
            display = city.display_name.lower()

            matched = False

            if zip_code and zip_code.startswith(normalized):
                matched = True
            elif city_name.startswith(normalized):
                matched = True
            elif display.startswith(normalized):
                matched = True
            elif len(parts) >= 2:
                city_part = " ".join(parts[:-1])
                state_part = parts[-1]
                if city_name.startswith(city_part) and (
                    state_code.startswith(state_part) or state_name.startswith(state_part)
                ):
                    matched = True

            if matched:
                startswith_matches.append(city)
                continue

            if (
                normalized in city_name
                or normalized in display
                or normalized in state_name
                or normalized in zip_code
            ):
                contains_matches.append(city)

        deduped: list[LocationResult] = []
        seen: set[tuple[str, str, str]] = set()

        for item in startswith_matches + contains_matches:
            key = (item.city.lower(), item.state.lower(), item.zip.lower())
            if key not in seen:
                seen.add(key)
                deduped.append(item)

        return deduped[:limit]

    def geocode_fallback(self, query: str, limit: int = 5) -> list[LocationResult]:
        query = query.strip()
        if len(query) < MIN_SEARCH_CHARS:
            return []

        try:
            response = requests.get(
                "https://geocoding-api.open-meteo.com/v1/search",
                params={
                    "name": query,
                    "count": limit,
                    "language": "en",
                    "format": "json",
                },
                timeout=8,
            )
            response.raise_for_status()
            payload = response.json()
        except Exception:
            return []

        results = payload.get("results", []) or []
        parsed: list[LocationResult] = []

        for item in results:
            country = str(item.get("country", "")).strip()
            if country and country.lower() not in {"united states", "usa", "us"}:
                continue

            parsed.append(
                LocationResult(
                    city=str(item.get("name", "")).strip(),
                    state=str(item.get("admin1", "")).strip(),
                    state_name=str(item.get("admin1", "")).strip(),
                    lat=float(item.get("latitude", 0.0) or 0.0),
                    lon=float(item.get("longitude", 0.0) or 0.0),
                    zip="",
                    country=country or "United States",
                    source="api",
                )
            )

        return parsed

    def autocomplete(self, query: str, limit: int = MAX_AUTOCOMPLETE_RESULTS) -> list[LocationResult]:
        local_results = self.search_local(query, limit=limit)

        if len(local_results) >= 3:
            return local_results[:limit]

        fallback_results = self.geocode_fallback(query, limit=limit)

        combined: list[LocationResult] = []
        seen: set[tuple[str, str]] = set()

        for item in local_results + fallback_results:
            key = (item.city.lower(), item.state.lower())
            if key not in seen:
                seen.add(key)
                combined.append(item)

        return combined[:limit]