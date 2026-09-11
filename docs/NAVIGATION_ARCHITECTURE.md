# Navigation architecture

## Provider boundary
`OpenSourceNavigationService` owns all external map-service calls. It uses a Nominatim-compatible `/search` endpoint for five cached destination suggestions and an OSRM-compatible `/route/v1/driving` endpoint for GeoJSON geometry, alternatives, legs, and steps. `DemoNavigationService` implements the same `autocomplete`, `place_details`, and `routes` contract with labelled fixture data. This makes an OSRM-to-Valhalla or Nominatim-to-Photon migration a backend-only concern.

## Request flow
```text
Leaflet + browser geolocation
  -> /api/navigation/places -> Nominatim-compatible provider
  -> /api/navigation/routes -> OSRM-compatible provider
  -> CarbonStride + transparent YuvaDrive scoring -> browser route comparison
```

The browser never holds a private provider key. Public endpoints remain configured on the backend only and can be replaced by environment variables.

## Scoring and CarbonStride
`carbonstride` applies configurable fuel-per-100-km and grams-CO₂-per-km assumptions. The YuvaDrive Safety Score begins at 96 and applies transparent distance, route-turn complexity, and average-speed-risk penalties, clamped to 60–98. It does not claim live weather, crash risk, traffic, speed-limit, or scientific validation. CarbonStride recommends the route that balances estimated CO₂, duration, and the score.

## Navigation lifecycle
The browser progresses through location loading/ready/error, destination search/selected, route loading/ready/error, navigation active, off-route/recalculating, and complete states. `watchPosition` updates the same Leaflet marker. A point-to-route estimate compares GPS positions against route geometry; when it exceeds the configured threshold, one recalculation is allowed per cooldown. Failed geolocation or provider calls retain a user-readable status and never expose a stack trace.
