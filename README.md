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

## Google Maps setup

The **Navigation** page (`/routes`) is integrated with the official Google Maps Platform: the Maps JavaScript API renders Google map tiles and controls in the browser, the server proxies **Places API (New)** autocomplete/place-details calls, and it proxies **Routes API** `computeRoutes` calls for driving alternatives and Google's encoded road polylines. Browser device GPS is requested on opening Navigation; its speed flows to YuvaDrive's existing safety coach. The UI deliberately labels unknown speed limits as unavailable rather than inventing a legal limit.

### Configure a real Google Maps experience

1. Create a Google Cloud project and attach billing where Google requires it.
2. Enable only **Maps JavaScript API**, **Places API (New)**, and **Routes API**.
3. Create an API key and put it in your local environment (copy `.env.example` as a reference; it is not loaded automatically):
   ```bash
   export GOOGLE_MAPS_API_KEY='your-key'
   export YUVADRIVE_DEMO_MODE=false
   ```
4. Restrict the key. The Maps JavaScript API requires an HTTP-referrer restriction for the deployed web origin. Because this application uses the same key for its server-side Places/Routes proxy, also restrict that key to the server's egress IP (or, preferably, use a separate restricted server key and extend `GoogleMapsService` configuration for production).
5. Start the application and visit `/routes`. Approve the browser location request. HTTPS is required by browsers for device location except on localhost.

The key is never committed. Places and Routes responses are proxied by the server so destination search and road-route requests do not place a server credential in application responses. The JavaScript Maps key must be delivered to the browser to load Google's SDK; treat it as a restricted browser key and never as a secret.

### Demo Mode

Without `GOOGLE_MAPS_API_KEY`, or with `YUVADRIVE_DEMO_MODE=true`, Navigation runs a fully labelled deterministic demo: destinations, curved simulated route geometry, GPS fallback, speed, ETA, and CarbonStride cards still work. It never claims that those values or tiles are live Google data. This project is a web FastAPI application, not a Flutter project; Android/iOS Maps SDK configuration is therefore not applicable. Web support is the existing supported client.

CarbonStride safety, fuel, and CO₂ values are configurable local YuvaDrive estimates (`YUVADRIVE_FUEL_L_PER_100KM` and `YUVADRIVE_CO2_GRAMS_PER_KM`); they are not Google-provided environmental or safety values. Google-mode distance, duration, route legs, and encoded route geometry originate from Routes API.
