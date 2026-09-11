# YuvaDrive — Traffic Rule Compliance Engine

YuvaDrive is a runnable, local-first safe-driving prototype. It turns speed awareness into supportive, multilingual-ready nudges; recognizes safe choices with private scores, streaks, challenges, and rewards; and compares seeded eco-route options. Its guiding principle is: **recognize safe behaviour, never shame.**

> **Demo only:** This project uses illustrative GPS, route, weather, rewards, and safety data. It is not a navigation, enforcement, insurance, emergency-response, or real-time driving-safety system.

## Run locally

```bash
python -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
uvicorn app:app --reload
```

Visit [http://127.0.0.1:8000](http://127.0.0.1:8000), then use the demo speed controls in Drive mode. No cloud account, API key, or paid infrastructure is required. See [docs/SETUP.md](docs/SETUP.md), [docs/DEMO_GUIDE.md](docs/DEMO_GUIDE.md), and [docs/API.md](docs/API.md).

## Included

- FastAPI REST API with interactive docs at `/docs`.
- SQLite-backed seeded profile, private trips, points, and preferences.
- Deterministic behaviour/nudge engine that always keeps the prototype functional.
- Responsive dashboard, drive HUD, route comparison, demo sign-in, and browser voice cues.
- API tests and database schema reference.

## Project documentation

- [Project audit](docs/PROJECT_AUDIT.md)
- [Architecture](docs/ARCHITECTURE.md)
- [Features](docs/FEATURES.md)
- [Database](docs/DATABASE.md)
