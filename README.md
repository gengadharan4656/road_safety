# YuvaDrive — Smart Driving & Safe Navigation

YuvaDrive is a FastAPI and vanilla-JavaScript prototype that combines open-source navigation with supportive safe-driving habits. It prioritizes **safety, awareness, positive reinforcement, and lower-impact choices**—never public shaming.

> **Prototype notice:** YuvaDrive Safety Scores, fuel, CO₂, route labels, rewards, and demo telemetry are illustrative configurable estimates. They are not legal speed limits, scientific safety ratings, real-time traffic, enforcement, insurance, or emergency guidance.

## Run locally

```bash
python -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
uvicorn app:app --reload
```

Open [http://127.0.0.1:8000](http://127.0.0.1:8000). Use a local server rather than `file://`: browser geolocation and API calls require an HTTP(S) origin. HTTPS is normally required for geolocation outside localhost.

## Features

- OpenStreetMap tiles rendered with Leaflet, including required OpenStreetMap attribution.
- Browser GPS current-location marker, live `watchPosition` updates, accuracy-aware graceful fallback, and a Re-center action.
- Debounced Nominatim destination search via the YuvaDrive backend and OSRM driving-route alternatives via a replaceable service abstraction.
- Clear route comparison for fastest, safest, eco, and balanced choices; selected routes show distance, duration, turns, YuvaDrive Safety Score, fuel, and CO₂ estimates.
- CarbonStride recommendation: **Safer. Greener. Smarter.**
- Start Navigation mode with remaining distance/time, next OSRM instruction where available, speed awareness (never a fabricated legal limit), off-route detection, and cooldown-based recalculation.
- Clearly labelled demo mode for GPS, network, and speech limitations; seeded Madurai destinations include Madurai Junction Railway Station.
- Existing dashboard, private progress, rewards, challenges, supportive multilingual safety nudges, trip recording, and demo profile are preserved.

## Navigation providers and attribution

The browser renders [OpenStreetMap](https://www.openstreetmap.org/) data through [Leaflet](https://leafletjs.com/). Destination search is proxied to [Nominatim](https://nominatim.org/) and driving routes to [OSRM](https://project-osrm.org/). The Leaflet control displays `© OpenStreetMap contributors` on the map.

The public services are convenient for small demos only. Respect their usage policies and do not use them as a high-volume production dependency. `navigation_services.py` isolates geocoding/routing behind `OpenSourceNavigationService`, so deployments can point to compliant hosted or self-hosted Nominatim/Photon and OSRM/Valhalla services.

## Configuration

Copy values from `.env.example` into your deployment environment. No API keys are required or stored by this project.

| Variable | Purpose |
|---|---|
| `YUVADRIVE_DEMO_MODE` | Set `true` to use deterministic, labelled demo search/routes. |
| `YUVADRIVE_GEOCODING_URL` | Nominatim-compatible provider base URL. |
| `YUVADRIVE_ROUTING_URL` | OSRM-compatible provider base URL. |
| `YUVADRIVE_FUEL_L_PER_100KM` | CarbonStride fuel assumption. |
| `YUVADRIVE_CO2_GRAMS_PER_KM` | CarbonStride CO₂ assumption. |
| `YUVADRIVE_OFF_ROUTE_THRESHOLD_METERS` | GPS distance threshold before route recalculation. |
| `YUVADRIVE_SEARCH_DEBOUNCE_MS` / `YUVADRIVE_ROUTE_COOLDOWN_MS` | Client request controls. |

## Demo flow

1. Open the dashboard and select **Start drive** or **Navigation**.
2. Allow location access, or continue with the visibly labelled Madurai demo position.
3. Search for `Madurai Railway Station`, select the suggestion, and compare the returned routes.
4. Select the CarbonStride route and press **Start Navigation**.
5. Review live speed awareness, remaining trip data, and the next instruction. GPS movement off the route triggers a cooldown-protected recalculation.

## Limitations and production deployment

- Public OSRM/Nominatim availability and rate limits can affect searches and routes; use caching, a backend proxy, monitoring, and self-hosted or contracted providers in production.
- GPS, `watchPosition`, speech synthesis/recognition availability, and accuracy vary by browser/device. Voice recognition is not required for navigation and must remain optional.
- OSRM public routing has no live traffic; route duration is not a traffic prediction. YuvaDrive has no authoritative speed-limit dataset, so it shows speed awareness rather than a legal limit.
- Improve production with self-hosted OSRM or Valhalla, compliant geocoding, real safety datasets, real-time traffic, map matching, richer maneuver guidance, and a native mobile client.

## Documentation

- [Project audit](docs/PROJECT_AUDIT.md)
- [Navigation architecture](docs/NAVIGATION_ARCHITECTURE.md)
- [API](docs/API.md)
- [Setup](docs/SETUP.md)
- [Implementation report](docs/IMPLEMENTATION_REPORT.md)
