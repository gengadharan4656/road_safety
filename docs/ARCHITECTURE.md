# Architecture

YuvaDrive is a FastAPI + Jinja prototype. `app.py` is the executable entry point and composes the HTTP API, local `SQLiteStore`, and deterministic `SafetyCoach`. SQLite is initialized automatically at `data/yuvadrive.db` (or `YUVADRIVE_DB_PATH`) and seeded with a private demo profile and recent trips.

```text
Browser UI -> FastAPI routes -> SQLiteStore -> SQLite
                         -> SafetyCoach (deterministic rules)
```

The API exposes driver-owned information only. Community progress is an aggregate goal, never an individual violation leaderboard. The safety coach selects supportive language and awards positive points for safe telemetry; it does not shame, rank, or publicly identify drivers.
