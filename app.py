"""YuvaDrive: a local-first traffic-rule compliance prototype.

Run with: uvicorn app:app --reload
The service deliberately uses deterministic safety rules and SQLite so the demo works
without cloud credentials or paid AI services.
"""
from __future__ import annotations

import os
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from threading import RLock
from typing import Literal

from fastapi import FastAPI, HTTPException, status
from fastapi.requests import Request
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, Field

ROOT = Path(__file__).parent
DB_PATH = Path(os.getenv("YUVADRIVE_DB_PATH", ROOT / "data" / "yuvadrive.db"))
DB_PATH.parent.mkdir(parents=True, exist_ok=True)

app = FastAPI(
    title="YuvaDrive API",
    version="2.0.0",
    description="Local-first safe-driving prototype. Demo data only; not for enforcement.",
)
app.mount("/static", StaticFiles(directory=ROOT / "static"), name="static")
templates = Jinja2Templates(directory=ROOT / "templates")
_db_lock = RLock()


class LoginRequest(BaseModel):
    email: str = Field(min_length=3, max_length=254)
    password: str = Field(min_length=1, max_length=128)


class TelemetryUpdate(BaseModel):
    speed_kmh: float = Field(ge=0, le=300)
    latitude: float = Field(default=12.9719, ge=-90, le=90)
    longitude: float = Field(default=77.5943, ge=-180, le=180)
    speed_limit_kmh: int | None = Field(default=None, ge=10, le=140)


class LanguagePreference(BaseModel):
    language: Literal["en", "hi", "kn"]


class SQLiteStore:
    """Tiny repository for a single seeded prototype profile."""

    def __init__(self, path: Path) -> None:
        self.path = path
        self.initialize()

    @contextmanager
    def connection(self):
        connection = sqlite3.connect(self.path)
        connection.row_factory = sqlite3.Row
        try:
            yield connection
            connection.commit()
        finally:
            connection.close()

    def initialize(self) -> None:
        with _db_lock, self.connection() as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS profiles (
                    id INTEGER PRIMARY KEY, name TEXT NOT NULL, points INTEGER NOT NULL,
                    safety_score INTEGER NOT NULL, streak_days INTEGER NOT NULL,
                    total_safe_km REAL NOT NULL
                );
                CREATE TABLE IF NOT EXISTS preferences (
                    profile_id INTEGER PRIMARY KEY, language TEXT NOT NULL DEFAULT 'en',
                    voice_enabled INTEGER NOT NULL DEFAULT 1
                );
                CREATE TABLE IF NOT EXISTS trips (
                    id INTEGER PRIMARY KEY AUTOINCREMENT, profile_id INTEGER NOT NULL,
                    started_at TEXT NOT NULL, duration_seconds INTEGER NOT NULL,
                    distance_km REAL NOT NULL, average_speed_kmh REAL NOT NULL,
                    safe_events INTEGER NOT NULL, points_earned INTEGER NOT NULL
                );
                """
            )
            conn.execute(
                "INSERT OR IGNORE INTO profiles VALUES (1, 'Aarav', 1240, 92, 6, 148.5)"
            )
            conn.execute("INSERT OR IGNORE INTO preferences VALUES (1, 'en', 1)")
            if not conn.execute("SELECT 1 FROM trips LIMIT 1").fetchone():
                conn.executemany(
                    "INSERT INTO trips (profile_id, started_at, duration_seconds, distance_km, average_speed_kmh, safe_events, points_earned) VALUES (1, ?, ?, ?, ?, ?, ?)",
                    [
                        ("2026-09-10T08:15:00+00:00", 1260, 8.4, 32.0, 14, 72),
                        ("2026-09-09T17:40:00+00:00", 900, 5.1, 29.0, 11, 55),
                        ("2026-09-08T09:05:00+00:00", 1140, 7.2, 31.0, 13, 68),
                    ],
                )

    def profile(self) -> dict:
        with self.connection() as conn:
            row = conn.execute("SELECT * FROM profiles WHERE id = 1").fetchone()
            language = conn.execute("SELECT language FROM preferences WHERE profile_id = 1").fetchone()[0]
        return {**dict(row), "language": language}

    def trips(self) -> list[dict]:
        with self.connection() as conn:
            rows = conn.execute("SELECT * FROM trips WHERE profile_id = 1 ORDER BY id DESC LIMIT 5").fetchall()
        return [dict(row) for row in rows]

    def set_language(self, language: str) -> None:
        with _db_lock, self.connection() as conn:
            conn.execute("UPDATE preferences SET language = ? WHERE profile_id = 1", (language,))

    def reward_safe_event(self, distance_increment: float = 0.0) -> int:
        with _db_lock, self.connection() as conn:
            conn.execute("UPDATE profiles SET points = points + 2, total_safe_km = total_safe_km + ? WHERE id = 1", (distance_increment,))
            return conn.execute("SELECT points FROM profiles WHERE id = 1").fetchone()[0]

    def complete_trip(self, telemetry: dict) -> dict:
        earned = max(25, min(100, 45 + int(telemetry["distance_km"] * 3)))
        with _db_lock, self.connection() as conn:
            conn.execute(
                "INSERT INTO trips (profile_id, started_at, duration_seconds, distance_km, average_speed_kmh, safe_events, points_earned) VALUES (1, ?, ?, ?, ?, ?, ?)",
                (datetime.now(timezone.utc).isoformat(), telemetry["trip_duration_seconds"], telemetry["distance_km"], telemetry["speed_kmh"], 12, earned),
            )
            conn.execute("UPDATE profiles SET points = points + ?, total_safe_km = total_safe_km + ? WHERE id = 1", (earned, telemetry["distance_km"]))
        return {"points_earned": earned, "message": "Trip saved. Your calm, attentive driving made a difference."}


class SafetyCoach:
    """Deterministic, supportive substitute for a cloud nudge model."""

    messages = {
        "en": {
            "safe": "Great pace. Keep scanning the road ahead.",
            "caution": "You are a little over the limit. Ease back to {limit} km/h when safe.",
            "warning": "Take a gentle reset: lift off the accelerator and return to {limit} km/h.",
        },
        "hi": {
            "safe": "बहुत बढ़िया गति। सड़क पर ध्यान बनाए रखें।",
            "caution": "आप सीमा से थोड़ा ऊपर हैं। सुरक्षित होने पर {limit} किमी/घं तक धीमे हों।",
            "warning": "धीरे से एक्सेलेरेटर छोड़ें और {limit} किमी/घं पर लौटें।",
        },
        "kn": {
            "safe": "ಉತ್ತಮ ವೇಗ. ರಸ್ತೆಯ ಮೇಲೆ ಗಮನ ಇರಲಿ.",
            "caution": "ನೀವು ಮಿತಿಗಿಂತ ಸ್ವಲ್ಪ ವೇಗವಾಗಿದ್ದೀರಿ. ಸುರಕ್ಷಿತವಾಗಿ {limit} ಕಿಮೀ/ಗಂ ಗೆ ಇಳಿಸಿ.",
            "warning": "ಮೃದುವಾಗಿ ವೇಗ ಕಡಿಮೆ ಮಾಡಿ {limit} ಕಿಮೀ/ಗಂ ಗೆ ಮರಳಿ.",
        },
    }

    def nudge(self, speed: float, limit: int, language: str) -> dict:
        if speed > limit + 10:
            severity, active, cue = "warning", True, "slow_down"
        elif speed > limit:
            severity, active, cue = "caution", True, "ease_back"
        else:
            severity, active, cue = "safe", False, ""
        return {
            "active": active,
            "severity": severity,
            "message": self.messages[language][severity].format(limit=limit),
            "audio_cue": cue,
            "principle": "Recognize safe behaviour. Never shame.",
        }


store = SQLiteStore(DB_PATH)
coach = SafetyCoach()
_telemetry = {
    "speed_kmh": 42.0, "speed_limit_kmh": 50, "latitude": 12.9719, "longitude": 77.5943,
    "trip_duration_seconds": 1125, "distance_km": 8.4, "updated_at": datetime.now(timezone.utc).isoformat(),
}


def telemetry_snapshot() -> dict:
    profile = store.profile()
    snapshot = _telemetry.copy()
    snapshot["safety_nudge"] = coach.nudge(snapshot["speed_kmh"], snapshot["speed_limit_kmh"], profile["language"])
    snapshot["language"] = profile["language"]
    return snapshot


@app.get("/", include_in_schema=False)
def home() -> RedirectResponse:
    return RedirectResponse("/dashboard", status_code=status.HTTP_302_FOUND)


@app.get("/dashboard", include_in_schema=False)
def dashboard_page(request: Request):
    return templates.TemplateResponse(request, "dashboard.html")


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


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "service": "yuvadrive", "storage": "sqlite"}


@app.post("/api/auth/login")
def login(credentials: LoginRequest) -> dict[str, str | bool]:
    if not credentials.email.strip() or not credentials.password.strip():
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    return {"authenticated": True, "user": credentials.email.strip(), "session_token": "demo-session-token"}


@app.get("/api/dashboard")
def dashboard() -> dict:
    profile = store.profile()
    return {
        "profile": {"name": profile["name"], "safety_score": profile["safety_score"], "streak_days": profile["streak_days"], "points": profile["points"], "total_safe_km": profile["total_safe_km"]},
        "reward": {"next_reward": "₹75 local café voucher", "points_to_next": max(0, 1500 - profile["points"])},
        "community_goal": {"label": "Campus safe-kilometre week", "progress": 742, "target": 1000, "message": "Your community is building safer roads together."},
        "recent_trips": store.trips(),
    }


@app.get("/api/telemetry/live")
def live_telemetry() -> dict:
    with _db_lock:
        return telemetry_snapshot()


@app.post("/api/telemetry/update")
def update_telemetry(update: TelemetryUpdate) -> dict:
    with _db_lock:
        _telemetry.update(update.model_dump(exclude_none=True))
        _telemetry["updated_at"] = datetime.now(timezone.utc).isoformat()
        if _telemetry["speed_kmh"] <= _telemetry["speed_limit_kmh"]:
            store.reward_safe_event(0.02)
        return telemetry_snapshot()


@app.post("/api/trips/complete")
def complete_trip() -> dict:
    with _db_lock:
        outcome = store.complete_trip(_telemetry)
    return outcome | {"trip": telemetry_snapshot()}


@app.get("/api/trips")
def trips() -> dict:
    return {"trips": store.trips()}


@app.get("/api/challenges")
def challenges() -> dict:
    return {"challenges": [
        {"id": "calm-commute", "title": "Calm commute", "description": "Complete 3 trips within the speed limit.", "progress": 2, "target": 3, "reward_points": 80, "joined": True},
        {"id": "phone-free", "title": "Phone-free focus", "description": "Keep drive mode active for 30 minutes this week.", "progress": 18, "target": 30, "reward_points": 100, "joined": False},
    ]}


@app.post("/api/challenges/{challenge_id}/join")
def join_challenge(challenge_id: str) -> dict:
    if challenge_id not in {"calm-commute", "phone-free"}:
        raise HTTPException(status_code=404, detail="Challenge not found")
    return {"joined": True, "challenge_id": challenge_id, "message": "You are in. Small, safe choices add up."}


@app.post("/api/preferences/language")
def set_language(preference: LanguagePreference) -> dict:
    store.set_language(preference.language)
    return {"language": preference.language, "message": "Voice nudge language updated."}


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
        "options": [
            {"name": "Green corridor", "duration_min": 21, "distance_km": 8.4, "co2_g": 720, "safety_score": 98, "recommended": True},
            {"name": "Express highway", "duration_min": 18, "distance_km": 9.1, "co2_g": 910, "safety_score": 82, "recommended": False},
        ],
    }
