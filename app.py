"""DRIVOZA demo service and server-rendered driving views."""

from __future__ import annotations

from datetime import datetime, timezone
from threading import Lock
from fastapi import FastAPI, HTTPException, status
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.requests import Request
from pydantic import BaseModel, Field

app = FastAPI(title="DRIVOZA API", version="1.0.0")
templates = Jinja2Templates(directory="templates")
_telemetry_lock = Lock()


class LoginRequest(BaseModel):
    email: str = Field(min_length=3, max_length=254)
    password: str = Field(min_length=1, max_length=128)


class TelemetryUpdate(BaseModel):
    speed_kmh: float = Field(ge=0, le=300)
    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)
    speed_limit_kmh: int | None = Field(default=None, ge=10, le=140)


_telemetry = {
    "speed_kmh": 42.0,
    "speed_limit_kmh": 50,
    "latitude": 12.9719,
    "longitude": 77.5943,
    "trip_duration_seconds": 1125,
    "distance_km": 8.4,
    "updated_at": datetime.now(timezone.utc).isoformat(),
}


def safety_nudge(speed_kmh: float, speed_limit_kmh: int) -> dict[str, str | bool]:
    if speed_kmh > speed_limit_kmh + 10:
        return {"active": True, "severity": "warning", "message": "Ease off the accelerator. You are well above the speed limit.", "audio_cue": "overspeed"}
    if speed_kmh > speed_limit_kmh:
        return {"active": True, "severity": "caution", "message": f"Slow down to {speed_limit_kmh} km/h for this road.", "audio_cue": "slow_down"}
    return {"active": False, "severity": "safe", "message": "Great pace. Keep scanning the road ahead.", "audio_cue": ""}


@app.get("/", include_in_schema=False)
def home() -> RedirectResponse:
    return RedirectResponse("/hud", status_code=status.HTTP_302_FOUND)


@app.get("/hud", include_in_schema=False)
def hud(request: Request):
    return templates.TemplateResponse(request, "hud.html")


@app.get("/routes", include_in_schema=False)
def routes(request: Request):
    return templates.TemplateResponse(request, "routes_map.html")


@app.get("/login", include_in_schema=False)
def login_page(request: Request):
    return templates.TemplateResponse(request, "login.html")


@app.get("/safety", include_in_schema=False)
def safety_page() -> RedirectResponse:
    return RedirectResponse("/hud#safety-nudge", status_code=status.HTTP_302_FOUND)


@app.post("/api/auth/login")
def login(credentials: LoginRequest) -> dict[str, str | bool]:
    """Create a demo session. Replace this check with an identity provider in production."""
    if not credentials.email.strip() or not credentials.password.strip():
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    return {"authenticated": True, "user": credentials.email.strip(), "session_token": "demo-session-token"}


@app.get("/api/telemetry/live")
def live_telemetry() -> dict:
    with _telemetry_lock:
        snapshot = _telemetry.copy()
    snapshot["safety_nudge"] = safety_nudge(snapshot["speed_kmh"], snapshot["speed_limit_kmh"])
    return snapshot


@app.post("/api/telemetry/update")
def update_telemetry(update: TelemetryUpdate) -> dict:
    with _telemetry_lock:
        _telemetry.update(update.model_dump(exclude_none=True))
        _telemetry["updated_at"] = datetime.now(timezone.utc).isoformat()
        snapshot = _telemetry.copy()
    snapshot["safety_nudge"] = safety_nudge(snapshot["speed_kmh"], snapshot["speed_limit_kmh"])
    return snapshot


@app.get("/api/routes/eco")
def eco_route() -> dict:
    return {
        "start": {"name": "Campus North Gate", "latitude": 12.9719, "longitude": 77.5943},
        "end": {"name": "Tech City Metro Hub", "latitude": 12.9654, "longitude": 77.6068},
        "waypoints": [
            {"name": "Green Avenue", "latitude": 12.9702, "longitude": 77.5970, "speed_limit_kmh": 40},
            {"name": "School crossing", "latitude": 12.9681, "longitude": 77.6005, "speed_limit_kmh": 30, "hazard": "School zone"},
            {"name": "Quiet boulevard", "latitude": 12.9667, "longitude": 77.6033, "speed_limit_kmh": 50},
        ],
    }
