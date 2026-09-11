# YuvaDrive project audit

## Current architecture
The repository is a small server-rendered Python prototype. `app.py` exposes a FastAPI application, holds mutable telemetry in process memory, and renders Jinja templates from `templates/`. The active UI is plain HTML with Tailwind and Leaflet loaded from CDNs. `requirements.txt` lists FastAPI, Uvicorn, and Jinja only. No Flutter/mobile project, database, environment configuration, test suite, CI, static asset pipeline, or backend package structure exists.

The four root `*.txt` files are uploaded HTML design explorations. They are not referenced by the running application, and include remote assets and inline Tailwind configuration.

## Existing features
- A demo login endpoint and login page.
- Live-speed telemetry read/update endpoints backed by an in-memory dictionary.
- A threshold-based overspeed nudge and browser text-to-speech.
- A Leaflet eco-route map with seeded waypoints.
- A compact, mobile-first drive HUD.

## Missing or incomplete features
- Product identity is still **DRIVOZA**, not YuvaDrive.
- No persistence, driver profile, trip lifecycle, trip history, safety score, rewards, challenges, streaks, analytics, multilingual nudge selection, or community-safe aggregate view.
- No API versioning, response schemas, OpenAPI metadata beyond FastAPI defaults, health check, or validation tests.
- Route data lacks measurable eco/safety comparisons.
- Login returns a fixed token and does not create a real authenticated session; it is appropriate only for a demo.
- Existing pages use externally hosted CDN assets, so the map/style experience needs network access.

## Broken features and risks
- Process restart loses all telemetry and any hypothetical driver state.
- A shared global telemetry object makes all visitors share one trip and is unsuitable for concurrent users.
- The old safety nudge can repeat voice output after changes without a configurable preference.
- Leaflet and Tailwind external CDN dependencies prevent a fully offline browser presentation.
- No credentials are currently stored (good), but any production authentication/telemetry use requires privacy, consent, retention, and security design.

## Technical debt
- All backend concerns are mixed in `app.py`; schemas, persistence, and safety rules are not isolated.
- HTML templates contain long, dense inline scripts and style dependencies.
- Design-source `.txt` files duplicate UI concepts and should be treated as reference material rather than runtime code.

## Recommended architecture
For this prototype, retain FastAPI and Jinja while introducing a small feature-oriented backend: a SQLite repository, deterministic behaviour/nudge service, typed Pydantic contracts, and explicit API endpoints. This remains runnable without paid services. For production, replace demo authentication with an identity provider, move SQLite to PostgreSQL/PostGIS, emit device telemetry through authenticated ingestion, and move analytics to privacy-reviewed aggregates. A Flutter client can consume the same REST contracts later; none exists to extend today.

## Implementation plan
1. Preserve the FastAPI entry point and add SQLite-backed demo state, safety scoring, rewards/challenges, route options, and language-aware deterministic nudges.
2. Build a responsive YuvaDrive dashboard/drive interface around those APIs; keep the existing drive/route/login pathways compatible.
3. Add docs, database schema, tests, setup/run helpers, health checks, and a seeded offline demo.
4. Verify API behavior and page rendering before release.

## Prototype limitations
- Safety calculations are illustrative and must not be used for enforcement, insurance, emergency response, or real-time driving decisions.
- The route geometry, speed limits, weather, GPS, and rewards are seeded demo data, not authoritative sources.
- Data is intentionally local SQLite with no real credentials or authentication.
- Voice is represented by browser speech synthesis; supported voices depend on the browser/device.
