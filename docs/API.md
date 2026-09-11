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
| GET | `/api/navigation/config` | Public navigation timing, mode, and attribution configuration |
| POST | `/api/navigation/places` | Search destinations through the configured geocoding provider |
| POST | `/api/navigation/places/{place_id}` | Resolve a selected destination from the provider cache |
| POST | `/api/navigation/routes` | Get OSRM/demo driving alternatives plus YuvaDrive estimates |
| POST | `/api/navigation/telemetry` | Update navigation-mode GPS/speed telemetry and receive a safety nudge |

Navigation responses clearly separate OSRM route data from YuvaDrive’s configurable fuel, CO₂, Eco, safety, and CarbonStride prototype estimates.
