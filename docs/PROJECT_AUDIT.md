# YuvaDrive project audit

## Audit scope and startup
This audit was completed before the open-source navigation implementation. YuvaDrive is a server-rendered **FastAPI + Jinja + vanilla JavaScript** web prototype. Start it with `./scripts/run` or `uvicorn app:app --reload`; `/` redirects to the main dashboard at `/dashboard`.

## Existing architecture
- `app.py` is the FastAPI entry point. It serves templates, static assets, API routes, a small SQLite repository, seeded demo profile/trip data, and the supportive `SafetyCoach`.
- `navigation_services.py` contains the route/search provider adapters and deterministic demo navigation fixture.
- `templates/` contains server-rendered HTML pages; `static/app.css` provides shared styling and `static/navigation.js` drives the navigation page.
- `data/yuvadrive.db` is created at runtime. `database/schema/sqlite.sql` documents the database schema.
- `tests/test_api.py` is the existing API test suite. `requirements.txt` lists FastAPI, Uvicorn, and Jinja2.

## Existing pages and reusable features
- `/dashboard`: safety snapshot, private trip history, community goal, and challenge preview.
- `/hud`: current-speed display, safety coaching, demo controls, voice synthesis cues, and trip completion.
- `/routes`: a route/search screen with browser GPS handling, a demo fallback, CarbonStride estimates, and navigation telemetry.
- `/login`: a deliberately simple demo sign-in acknowledgement.
- Existing reusable backend pieces include `SQLiteStore`, `SafetyCoach`, `carbonstride`, telemetry endpoints, trip persistence, preference/language support, and the demo navigation service.

## Existing APIs and integrations
- Local APIs cover authentication acknowledgement, dashboard data, telemetry, trips, challenges, language preferences, static eco-route data, and navigation search/routing/telemetry.
- SQLite is the only database integration. Authentication is demo-only and no external credentials are stored.
- The pre-change navigation implementation referenced a proprietary map/search/route stack. It must be replaced, not retained, to meet the open-source navigation requirement.

## Dependencies and assets
- Runtime dependencies: FastAPI, Uvicorn, Jinja2, and HTTPX.
- UI dependencies currently use external browser CDNs only where needed. Leaflet and its CSS will be added for OpenStreetMap rendering.
- There is no React, Flutter, bundler, component framework, CI configuration, or compiled asset pipeline. Root `*.txt` files are design references, not executable application files.

## Files to modify
- `app.py`: replace the proprietary navigation configuration/service selection with open-source provider configuration and navigation APIs.
- `navigation_services.py`: provide Nominatim and OSRM adapters, normalized route results, and a separate demo fallback.
- `templates/routes_map.html`, `static/navigation.js`, and `static/app.css`: render the Leaflet/OpenStreetMap navigation experience while retaining YuvaDrive styling and existing page routes.
- `README.md`, `.env.example`, and `docs/API.md`: document the revised implementation and configuration.

## New files to add
- `docs/NAVIGATION_ARCHITECTURE.md`: provider abstractions, scoring and demo boundaries.
- `docs/IMPLEMENTATION_REPORT.md`: final implementation summary and limitations.

## Risks and mitigations
- Public Nominatim and OSRM instances are suitable only for low-volume demos; requests are debounced client-side and cached/abstracted server-side so production can use compliant/self-hosted providers.
- Browser GPS and speech recognition depend on user permission, HTTPS (except localhost), hardware, and browser support. A clearly marked demo mode remains available.
- OSRM does not provide real-time traffic or legal speed limits. Fuel, CO₂, and safety values are labelled YuvaDrive estimates; speed is awareness-only without authoritative speed-limit data.
- Navigation geometry and external network calls can fail. The UI must present recoverable messages and never expose raw errors.

## Implementation plan
1. Replace the legacy provider code with Nominatim, OSRM, and a deterministic demo adapter behind a common interface.
2. Add Leaflet with OpenStreetMap attribution and rework `/routes` to use geolocation, destination search, route alternatives, scoring, and CarbonStride comparison.
3. Add active navigation, marker updates, recentering, distance-to-route checks, cooldown-based recalculation, speed awareness, and optional browser voice assistance.
4. Preserve dashboard/HUD/profile functionality and link their navigation actions to the upgraded screen.
5. Update configuration, docs, API tests, and README; run automated tests and browser-level smoke checks.
