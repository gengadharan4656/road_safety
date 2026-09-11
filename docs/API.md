# API

All endpoints are prototype endpoints and return JSON. Interactive documentation is available at `/docs`.

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/health` | Service status |
| POST | `/api/auth/login` | Demo sign-in acknowledgement |
| GET | `/api/dashboard` | Profile, score, streak, reward and community summary |
| GET | `/api/telemetry/live` | Current drive telemetry plus supportive nudge |
| POST | `/api/telemetry/update` | Validate and record a telemetry update |
| POST | `/api/trips/complete` | Save a demo trip and return earned points |
| GET | `/api/trips` | Recent private trip summaries |
| GET | `/api/challenges` | Positive driving challenges |
| POST | `/api/challenges/{id}/join` | Join a challenge |
| GET | `/api/routes/eco` | Seeded safety/eco route alternatives |
| POST | `/api/preferences/language` | Set `en`, `hi`, or `kn` nudge language |
