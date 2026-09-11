"""Replaceable open-source navigation providers for YuvaDrive.

Public Nominatim and OSRM endpoints are intentionally configured for prototype
traffic only. Production should configure compliant, preferably self-hosted,
providers through environment variables.
"""
from __future__ import annotations

import asyncio
import json
import math
import os
from urllib import error as urlerror
from urllib import parse as urlparse
from urllib import request as urlrequest
from dataclasses import dataclass
from typing import Any

class NavigationServiceError(Exception):
    """A recoverable upstream navigation error safe to show to a driver."""


@dataclass(frozen=True)
class LocationPoint:
    latitude: float
    longitude: float


@dataclass(frozen=True)
class Destination:
    place_id: str
    name: str
    address: str
    point: LocationPoint


class OpenSourceNavigationService:
    """Nominatim geocoding plus OSRM driving routes behind one provider API."""

    def __init__(self, *, geocoding_url: str | None = None, routing_url: str | None = None) -> None:
        self.geocoding_url = (geocoding_url or os.getenv("YUVADRIVE_GEOCODING_URL", "https://nominatim.openstreetmap.org")).rstrip("/")
        self.routing_url = (routing_url or os.getenv("YUVADRIVE_ROUTING_URL", "https://router.project-osrm.org")).rstrip("/")
        self._destinations: dict[str, Destination] = {}

    async def autocomplete(self, query: str) -> list[dict[str, str]]:
        try:
            records = await _get_json(f"{self.geocoding_url}/search", {"q": query, "format": "jsonv2", "addressdetails": 1, "limit": 5}, timeout=8)
        except (urlerror.URLError, urlerror.HTTPError, TimeoutError, ValueError, json.JSONDecodeError) as error:
            raise NavigationServiceError("Destination search is temporarily unavailable. Try again or use Demo Mode.") from error
        suggestions = []
        for record in records:
            try:
                place_id = f"osm-{record['osm_type']}-{record['osm_id']}"
                point = LocationPoint(float(record["lat"]), float(record["lon"]))
            except (KeyError, TypeError, ValueError):
                continue
            display_name = record.get("display_name", "Destination")
            name, _, address = display_name.partition(",")
            destination = Destination(place_id, name.strip() or "Destination", address.strip() or display_name, point)
            self._destinations[place_id] = destination
            suggestions.append({"place_id": place_id, "name": destination.name, "address": destination.address})
        return suggestions

    async def place_details(self, place_id: str) -> Destination:
        destination = self._destinations.get(place_id)
        if not destination:
            raise NavigationServiceError("That destination has expired. Search for it again.")
        return destination

    async def routes(self, origin: LocationPoint, destination: Destination) -> list[dict[str, Any]]:
        coordinates = f"{origin.longitude},{origin.latitude};{destination.point.longitude},{destination.point.latitude}"
        try:
            data = await _get_json(f"{self.routing_url}/route/v1/driving/{coordinates}", {"alternatives": "true", "overview": "full", "geometries": "geojson", "steps": "true"}, timeout=12)
        except (urlerror.URLError, urlerror.HTTPError, TimeoutError, ValueError, json.JSONDecodeError) as error:
            raise NavigationServiceError("Routing is temporarily unavailable. Try again or switch to Demo Mode.") from error
        if data.get("code") != "Ok" or not data.get("routes"):
            raise NavigationServiceError("No drivable route could be found. Try another destination.")
        routes = []
        for index, route in enumerate(data["routes"]):
            coordinates_data = route.get("geometry", {}).get("coordinates", [])
            points = [{"lat": lat, "lng": lng} for lng, lat in coordinates_data if isinstance(lat, (int, float)) and isinstance(lng, (int, float))]
            if len(points) < 2:
                continue
            routes.append({"id": f"osrm-{index}", "distance_meters": round(route.get("distance", 0)), "duration_seconds": round(route.get("duration", 0)), "points": points, "source": "osrm", "legs": route.get("legs", [])})
        if not routes:
            raise NavigationServiceError("Routing returned an incomplete route. Please try again.")
        return routes


class DemoNavigationService:
    """Deterministic, clearly labelled fixture data for offline demonstrations."""

    destinations = [
        Destination("demo-madurai-junction", "Madurai Junction Railway Station", "Madurai, Tamil Nadu, India", LocationPoint(9.9190, 78.1190)),
        Destination("demo-meenakshi", "Meenakshi Amman Temple", "Madurai, Tamil Nadu, India", LocationPoint(9.9195, 78.1193)),
        Destination("demo-chennai-central", "Chennai Central", "Chennai, Tamil Nadu, India", LocationPoint(13.0827, 80.2707)),
        Destination("demo-anna-nagar", "Anna Nagar", "Chennai, Tamil Nadu, India", LocationPoint(13.0850, 80.2101)),
    ]

    async def autocomplete(self, query: str) -> list[dict[str, str]]:
        terms = query.lower().split()
        matches = [d for d in self.destinations if all(term in f"{d.name} {d.address}".lower() for term in terms)]
        return [{"place_id": d.place_id, "name": d.name, "address": d.address} for d in matches]

    async def place_details(self, place_id: str) -> Destination:
        for destination in self.destinations:
            if destination.place_id == place_id:
                return destination
        raise NavigationServiceError("Demo destination was not found.")

    async def routes(self, origin: LocationPoint, destination: Destination) -> list[dict[str, Any]]:
        midpoint = LocationPoint((origin.latitude + destination.point.latitude) / 2 + 0.004, (origin.longitude + destination.point.longitude) / 2 - 0.004)
        variants = [[origin, midpoint, destination.point], [origin, LocationPoint(midpoint.latitude - 0.006, midpoint.longitude + 0.008), destination.point]]
        output = []
        for index, points in enumerate(variants):
            distance = _path_distance(points) * (1.12 + index * 0.08)
            output.append({"id": f"demo-{index}", "distance_meters": round(distance), "duration_seconds": round(distance / (8.5 - index)), "points": [{"lat": point.latitude, "lng": point.longitude} for point in points], "source": "demo", "legs": []})
        return output


def _path_distance(points: list[LocationPoint]) -> float:
    return sum(_haversine(a, b) for a, b in zip(points, points[1:]))


async def _get_json(url: str, params: dict[str, str | int], *, timeout: int) -> Any:
    """Make a bounded provider request without adding a runtime HTTP dependency."""
    query = urlparse.urlencode(params)
    request = urlrequest.Request(f"{url}?{query}", headers={"User-Agent": "YuvaDrive-prototype/1.0 (navigation demo)", "Accept": "application/json"})

    def send() -> Any:
        with urlrequest.urlopen(request, timeout=timeout) as response:
            return json.loads(response.read())

    return await asyncio.to_thread(send)


def _haversine(a: LocationPoint, b: LocationPoint) -> float:
    radius = 6_371_000
    d_lat, d_lng = math.radians(b.latitude - a.latitude), math.radians(b.longitude - a.longitude)
    value = math.sin(d_lat / 2) ** 2 + math.cos(math.radians(a.latitude)) * math.cos(math.radians(b.latitude)) * math.sin(d_lng / 2) ** 2
    return 2 * radius * math.asin(math.sqrt(value))
