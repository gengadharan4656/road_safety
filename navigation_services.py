"""Google Maps Platform and demo navigation adapters for YuvaDrive.

The production adapters proxy Places API (New) and Routes API calls so the
server-side key is never copied into route/search responses.  The browser key
is separately used only to load the official Maps JavaScript API.
"""
from __future__ import annotations

import asyncio
import json as jsonlib
import math
import os
from urllib import error as urlerror
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


def decode_polyline(encoded: str) -> list[dict[str, float]]:
    """Decode Google's Encoded Polyline Algorithm Format into map coordinates."""
    points: list[dict[str, float]] = []
    index = latitude = longitude = 0
    while index < len(encoded):
        values: list[int] = []
        for _ in range(2):
            result = shift = 0
            while True:
                if index >= len(encoded):
                    raise ValueError("Invalid encoded polyline")
                byte = ord(encoded[index]) - 63
                index += 1
                result |= (byte & 0x1F) << shift
                shift += 5
                if byte < 0x20:
                    break
            values.append(~(result >> 1) if result & 1 else result >> 1)
        latitude += values[0]
        longitude += values[1]
        points.append({"lat": latitude / 1e5, "lng": longitude / 1e5})
    return points


def encode_polyline(points: list[LocationPoint]) -> str:
    """Small encoder used only for clearly labelled, local demo route data."""
    output: list[str] = []
    previous_lat = previous_lng = 0
    for point in points:
        for value, previous in ((round(point.latitude * 1e5), previous_lat), (round(point.longitude * 1e5), previous_lng)):
            delta = value - previous
            shifted = ~(delta << 1) if delta < 0 else delta << 1
            while shifted >= 0x20:
                output.append(chr((0x20 | (shifted & 0x1F)) + 63))
                shifted >>= 5
            output.append(chr(shifted + 63))
        previous_lat, previous_lng = round(point.latitude * 1e5), round(point.longitude * 1e5)
    return "".join(output)


class GoogleMapsService:
    def __init__(self, api_key: str | None = None) -> None:
        self.api_key = api_key or os.getenv("GOOGLE_MAPS_API_KEY", "")

    @property
    def configured(self) -> bool:
        return bool(self.api_key)

    async def _request(self, method: str, url: str, *, headers: dict[str, str] | None = None, json: dict | None = None) -> dict:
        if not self.configured:
            raise NavigationServiceError("Google Maps is not configured. Switch to Demo Mode or add GOOGLE_MAPS_API_KEY.")
        combined_headers = {"X-Goog-Api-Key": self.api_key, **(headers or {})}
        body = None if json is None else jsonlib.dumps(json).encode("utf-8")
        if body is not None:
            combined_headers["Content-Type"] = "application/json"

        def send() -> dict:
            request = urlrequest.Request(url, data=body, headers=combined_headers, method=method)
            with urlrequest.urlopen(request, timeout=10) as response:
                return jsonlib.loads(response.read())
        try:
            return await asyncio.to_thread(send)
        except (urlerror.URLError, urlerror.HTTPError, TimeoutError, ValueError) as error:
            raise NavigationServiceError("Google Maps could not complete that request. Check API enablement, billing, key restrictions, and try again.") from error

    async def autocomplete(self, query: str) -> list[dict[str, str]]:
        data = await self._request("POST", "https://places.googleapis.com/v1/places:autocomplete", headers={"X-Goog-FieldMask": "suggestions.placePrediction.placeId,suggestions.placePrediction.text,suggestions.placePrediction.structuredFormat"}, json={"input": query})
        results = []
        for suggestion in data.get("suggestions", []):
            prediction = suggestion.get("placePrediction")
            if not prediction:
                continue
            structured = prediction.get("structuredFormat", {})
            results.append({"place_id": prediction["placeId"], "name": structured.get("mainText", {}).get("text", prediction.get("text", {}).get("text", "Place")), "address": structured.get("secondaryText", {}).get("text", "")})
        return results

    async def place_details(self, place_id: str) -> Destination:
        data = await self._request("GET", f"https://places.googleapis.com/v1/places/{place_id}", headers={"X-Goog-FieldMask": "id,displayName,formattedAddress,location"})
        location = data.get("location")
        if not location:
            raise NavigationServiceError("Google Places did not return a location for that destination.")
        return Destination(data.get("id", place_id), data.get("displayName", {}).get("text", "Destination"), data.get("formattedAddress", ""), LocationPoint(location["latitude"], location["longitude"]))

    async def routes(self, origin: LocationPoint, destination: Destination) -> list[dict[str, Any]]:
        payload = {"origin": {"location": {"latLng": {"latitude": origin.latitude, "longitude": origin.longitude}}}, "destination": {"placeId": destination.place_id}, "travelMode": "DRIVE", "computeAlternativeRoutes": True, "languageCode": "en-US", "units": "METRIC"}
        data = await self._request("POST", "https://routes.googleapis.com/directions/v2:computeRoutes", headers={"X-Goog-FieldMask": "routes.duration,routes.distanceMeters,routes.polyline.encodedPolyline,routes.legs"}, json=payload)
        routes = []
        for index, route in enumerate(data.get("routes", [])):
            encoded = route.get("polyline", {}).get("encodedPolyline")
            if not encoded:
                continue
            routes.append({"id": f"google-{index}", "distance_meters": route.get("distanceMeters", 0), "duration_seconds": round(float(str(route.get("duration", "0s")).removesuffix("s"))), "encoded_polyline": encoded, "points": decode_polyline(encoded), "source": "google", "legs": route.get("legs", [])})
        if not routes:
            raise NavigationServiceError("Google Routes did not find a drivable route for this destination.")
        return routes


class DemoNavigationService:
    """Deterministic, clearly labelled development data; never a Google response."""
    destinations = [
        Destination("demo-meenakshi", "Meenakshi Amman Temple", "Madurai, Tamil Nadu", LocationPoint(9.9195, 78.1193)),
        Destination("demo-chennai-central", "Chennai Central", "Chennai, Tamil Nadu", LocationPoint(13.0827, 80.2707)),
        Destination("demo-anna-nagar", "Anna Nagar", "Chennai, Tamil Nadu", LocationPoint(13.0850, 80.2101)),
    ]

    async def autocomplete(self, query: str) -> list[dict[str, str]]:
        needle = query.lower()
        matches = [d for d in self.destinations if needle in f"{d.name} {d.address}".lower()]
        return [{"place_id": d.place_id, "name": d.name, "address": d.address} for d in matches]

    async def place_details(self, place_id: str) -> Destination:
        for destination in self.destinations:
            if destination.place_id == place_id:
                return destination
        raise NavigationServiceError("Demo destination was not found.")

    async def routes(self, origin: LocationPoint, destination: Destination) -> list[dict[str, Any]]:
        # Curved fixture geometry intentionally represents a simulated road, not live data.
        midpoint = LocationPoint((origin.latitude + destination.point.latitude) / 2 + .004, (origin.longitude + destination.point.longitude) / 2 - .004)
        variants = [[origin, midpoint, destination.point], [origin, LocationPoint(midpoint.latitude - .006, midpoint.longitude + .008), destination.point]]
        output = []
        for index, points in enumerate(variants):
            distance = _path_distance(points) * (1.12 + index * .08)
            encoded = encode_polyline(points)
            output.append({"id": f"demo-{index}", "distance_meters": round(distance), "duration_seconds": round(distance / (8.5 - index)), "encoded_polyline": encoded, "points": decode_polyline(encoded), "source": "demo", "legs": []})
        return output


def _path_distance(points: list[LocationPoint]) -> float:
    return sum(_haversine(a, b) for a, b in zip(points, points[1:]))


def _haversine(a: LocationPoint, b: LocationPoint) -> float:
    radius = 6371000
    d_lat, d_lng = math.radians(b.latitude - a.latitude), math.radians(b.longitude - a.longitude)
    value = math.sin(d_lat / 2) ** 2 + math.cos(math.radians(a.latitude)) * math.cos(math.radians(b.latitude)) * math.sin(d_lng / 2) ** 2
    return 2 * radius * math.asin(math.sqrt(value))
