/* YuvaDrive NavigationController: Leaflet UI -> YuvaDrive API -> OSM services. */
(() => {
  const $ = id => document.getElementById(id);
  const input = $('destinationInput'), suggestions = $('suggestions'), searchStatus = $('searchStatus');
  let map, currentMarker, destinationMarker, routeLines = [], watchId, searchTimer;
  let position = {lat: 9.9252, lng: 78.1198, speed: 0, accuracy: null}; // Madurai demo fallback only
  let selectedDestination, selectedRoutes = [], selectedRoute, navigating = false, lastOffRoute = 0;
  let config = {off_route_threshold_meters: 65, search_debounce_ms: 350, route_recalculation_cooldown_ms: 30000};

  const request = (url, options = {}) => fetch(url, {headers: {'Content-Type': 'application/json'}, ...options}).then(async response => {
    const body = await response.json();
    if (!response.ok) throw new Error(body.detail || 'Something went wrong. Please try again.');
    return body;
  });
  const escapeHtml = value => String(value).replace(/[&<>'"]/g, char => ({'&':'&amp;','<':'&lt;','>':'&gt;',"'":'&#39;','"':'&quot;'}[char]));
  const km = meters => `${(meters / 1000).toFixed(1)} km`;
  const mins = seconds => `${Math.max(1, Math.round(seconds / 60))} min`;
  const notice = message => { const box = $('notice'); box.textContent = message; box.hidden = false; window.clearTimeout(notice.timer); notice.timer = window.setTimeout(() => box.hidden = true, 5500); };
  const point = coords => [coords.lat, coords.lng];

  function initMap() {
    map = L.map('map', {zoomControl: false}).setView(point(position), 14);
    L.control.zoom({position: 'bottomright'}).addTo(map);
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {maxZoom: 19, attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap contributors</a>'}).addTo(map);
    updateCurrentMarker();
  }
  function markerIcon(symbol, className) { return L.divIcon({className: `yuva-marker ${className}`, html: symbol, iconSize: [34, 34], iconAnchor: [17, 17]}); }
  function updateCurrentMarker() {
    if (!currentMarker) currentMarker = L.marker(point(position), {icon: markerIcon('●', 'current'), title: 'Current location'}).addTo(map).bindTooltip('Current location');
    else currentMarker.setLatLng(point(position));
  }
  function fitRoute(route) { if (route?.points?.length) map.fitBounds(L.latLngBounds(route.points.map(point)), {padding: [70, 70], maxZoom: 16}); }
  function drawRoutes() {
    routeLines.forEach(line => line.remove());
    routeLines = selectedRoutes.map(route => L.polyline(route.points.map(point), {color: route.id === selectedRoute.id ? '#1659d4' : '#8090a6', opacity: route.id === selectedRoute.id ? 1 : .55, weight: route.id === selectedRoute.id ? 7 : 4}).addTo(map));
    fitRoute(selectedRoute);
  }
  function routeType(route) {
    const fastest = selectedRoutes.reduce((best, item) => item.duration_seconds < best.duration_seconds ? item : best, selectedRoutes[0]);
    const safest = selectedRoutes.reduce((best, item) => item.safety_score > best.safety_score ? item : best, selectedRoutes[0]);
    const eco = selectedRoutes.reduce((best, item) => item.estimated_co2_grams < best.estimated_co2_grams ? item : best, selectedRoutes[0]);
    if (route.id === safest.id) return 'SAFEST';
    if (route.id === eco.id) return 'ECO';
    return route.id === fastest.id ? 'FASTEST' : 'BALANCED';
  }
  function routePanel() {
    const route = selectedRoute, fastest = selectedRoutes.reduce((best, item) => item.duration_seconds < best.duration_seconds ? item : best, selectedRoutes[0]);
    const savedFuel = Math.max(0, fastest.estimated_fuel_litres - route.estimated_fuel_litres).toFixed(2);
    const savedCo2 = Math.max(0, (fastest.estimated_co2_grams - route.estimated_co2_grams) / 1000).toFixed(2);
    $('routePanel').hidden = false;
    $('routePanel').innerHTML = `<h2 class="route-title">📍 ${escapeHtml(selectedDestination.name)}</h2><div class="muted">${escapeHtml(selectedDestination.address)}</div><div class="route-meta">${km(route.distance_meters)} · ${mins(route.duration_seconds)}</div><div class="route-choices">${selectedRoutes.map(item => `<button class="route-choice ${item.id === route.id ? 'selected' : ''}" data-route="${escapeHtml(item.id)}"><b>${routeType(item)}</b><br><small>${km(item.distance_meters)} · ${mins(item.duration_seconds)}</small><br><small>Safety ${item.safety_score} · Eco ${item.eco_score}</small></button>`).join('')}</div><div class="carbon-card"><b>🌱 CARBONSTRIDE · Safer. Greener. Smarter.</b><br><small>${route.carbonstride_recommended ? `Recommended. Saves approximately ${savedFuel} L fuel and ${savedCo2} kg CO₂ versus the fastest route.` : 'Choose the highlighted recommendation for YuvaDrive’s balanced safety and eco estimate.'}</small></div><p class="disclaimer">Safety ${route.safety_score}/100 · Fuel ${route.estimated_fuel_litres.toFixed(2)} L · CO₂ ${(route.estimated_co2_grams / 1000).toFixed(2)} kg. ${escapeHtml(route.estimate_source)}</p><button id="startDrive" class="button wide-button">START NAVIGATION</button>`;
    document.querySelectorAll('[data-route]').forEach(button => button.onclick = () => { selectedRoute = selectedRoutes.find(routeItem => routeItem.id === button.dataset.route); drawRoutes(); routePanel(); });
    $('startDrive').onclick = startDrive;
  }
  async function selectPlace(placeId, isRecalculation = false) {
    try {
      searchStatus.hidden = false; searchStatus.textContent = isRecalculation ? 'Recalculating safer route…' : 'Getting destination and road routes…'; suggestions.innerHTML = '';
      const details = await request(`/api/navigation/places/${encodeURIComponent(placeId)}`, {method: 'POST'});
      selectedDestination = details; input.value = details.name; $('clearSearch').hidden = false;
      if (destinationMarker) destinationMarker.remove();
      destinationMarker = L.marker([details.latitude, details.longitude], {icon: markerIcon('◆', 'destination'), title: details.name}).addTo(map).bindTooltip(details.name);
      const result = await request('/api/navigation/routes', {method: 'POST', body: JSON.stringify({origin_latitude: position.lat, origin_longitude: position.lng, place_id: placeId})});
      selectedRoutes = result.routes; selectedRoute = result.routes.find(route => route.carbonstride_recommended) || result.routes[0]; drawRoutes(); routePanel(); searchStatus.hidden = true;
      if (isRecalculation) notice('Your route has been refreshed. Drive safely.');
    } catch (error) { searchStatus.textContent = error.message; searchStatus.hidden = false; }
  }
  input.oninput = () => {
    window.clearTimeout(searchTimer); const query = input.value.trim(); $('clearSearch').hidden = !query;
    if (query.length < 2) { suggestions.innerHTML = ''; searchStatus.hidden = true; return; }
    searchTimer = window.setTimeout(async () => {
      try {
        searchStatus.hidden = false; searchStatus.textContent = 'Searching destinations…';
        const result = await request('/api/navigation/places', {method: 'POST', body: JSON.stringify({query})});
        searchStatus.hidden = true;
        suggestions.innerHTML = result.suggestions.length ? result.suggestions.map(item => `<button class="suggestion" data-place="${escapeHtml(item.place_id)}"><span>📍</span><span><b>${escapeHtml(item.name)}</b><small>${escapeHtml(item.address)}</small></span></button>`).join('') : '<div class="search-status">No destinations found. Try another search or Demo Mode.</div>';
        document.querySelectorAll('[data-place]').forEach(button => button.onclick = () => selectPlace(button.dataset.place));
      } catch (error) { searchStatus.textContent = error.message; searchStatus.hidden = false; }
    }, config.search_debounce_ms);
  };
  $('clearSearch').onclick = () => { input.value = ''; suggestions.innerHTML = ''; $('clearSearch').hidden = true; input.focus(); };
  $('voiceSearch').onclick = () => {
    const Recognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!Recognition) return notice('Voice assistance is not supported in this browser.');
    const recognition = new Recognition(); recognition.lang = navigator.language || 'en-IN'; recognition.interimResults = false;
    recognition.onresult = event => { input.value = event.results[0][0].transcript.replace(/^(take me to|navigate to|find)\s+/i, ''); input.dispatchEvent(new Event('input')); notice('Finding a safe route for you.'); };
    recognition.onerror = () => notice('Voice search could not hear a destination. Try typing it instead.'); recognition.start();
  };
  $('recenter').onclick = () => map.panTo(point(position));

  const radians = degrees => degrees * Math.PI / 180;
  function distanceMeters(a, b) { const r = 6371000, dLat = radians(b.lat - a.lat), dLng = radians(b.lng - a.lng); const value = Math.sin(dLat / 2) ** 2 + Math.cos(radians(a.lat)) * Math.cos(radians(b.lat)) * Math.sin(dLng / 2) ** 2; return 2 * r * Math.asin(Math.sqrt(value)); }
  function distanceToRouteMeters(location, route) { return Math.min(...route.points.map(routePoint => distanceMeters(location, routePoint))); }
  function nextStep() { const steps = selectedRoute?.legs?.flatMap(leg => leg.steps || []) || []; return steps[0]?.maneuver?.instruction || 'Continue on your selected route'; }
  async function updateDrive() {
    if (!selectedRoute) return;
    const destination = {lat: selectedDestination.latitude, lng: selectedDestination.longitude};
    const remaining = Math.min(selectedRoute.distance_meters, distanceMeters(position, destination) * 1.15);
    const seconds = selectedRoute.duration_seconds * remaining / selectedRoute.distance_meters;
    $('drivePanel').innerHTML = `<div class="remaining">SAFE DRIVING MODE · ${km(remaining)} remaining</div><div><small>Remaining time</small><b>${mins(seconds)}</b></div><div><small>Current speed</small><b>${Math.round(position.speed)} km/h</b></div><div><small>Safety status</small><b>Awareness active</b></div><div><small>Next</small><b>${escapeHtml(nextStep())}</b></div><div><small>Speed awareness</small><b>Legal limit unavailable</b></div>`;
    try { const telemetry = await request('/api/navigation/telemetry', {method: 'POST', body: JSON.stringify({speed_kmh: position.speed, latitude: position.lat, longitude: position.lng, distance_remaining_meters: remaining})}); if (telemetry.safety_nudge.active) notice(telemetry.safety_nudge.message); } catch (_) { /* Safety telemetry is non-blocking. */ }
    if (remaining < 45) { navigating = false; $('drivePanel').hidden = true; notice('Navigation complete. Great job arriving safely.'); }
  }
  function gpsSuccess(gps) {
    position = {lat: gps.coords.latitude, lng: gps.coords.longitude, speed: Math.max(0, gps.coords.speed || 0) * 3.6, accuracy: gps.coords.accuracy}; updateCurrentMarker();
    if (navigating) { updateDrive(); if (distanceToRouteMeters(position, selectedRoute) > config.off_route_threshold_meters && Date.now() - lastOffRoute > config.route_recalculation_cooldown_ms) { lastOffRoute = Date.now(); notice('You appear to be off route. Recalculating route…'); selectPlace(selectedDestination.place_id, true); } }
  }
  function gpsError(error) { const messages = {1: 'Location access is required for live navigation. Demo location remains active.', 2: 'Location is unavailable. Demo location remains active.', 3: 'Location request timed out. Demo location remains active.'}; notice(messages[error.code] || 'Location is unavailable. Demo location remains active.'); }
  function beginLocation() { if (!navigator.geolocation) return notice('Geolocation is not supported in this browser. Demo location remains active.'); navigator.geolocation.getCurrentPosition(gps => { gpsSuccess(gps); map.panTo(point(position)); }, gpsError, {enableHighAccuracy: true, timeout: 10000, maximumAge: 5000}); watchId = navigator.geolocation.watchPosition(gpsSuccess, gpsError, {enableHighAccuracy: true, timeout: 15000, maximumAge: 3000}); }
  function startDrive() { navigating = true; $('routePanel').hidden = true; $('drivePanel').hidden = false; updateDrive(); notice('Navigation started. Keep your attention on the road.'); }
  async function boot() { config = {...config, ...await request('/api/navigation/config')}; $('modeBadge').textContent = config.mode === 'demo' ? 'DEMO MODE · SIMULATED DATA' : 'OPENSTREETMAP · LIVE GPS'; $('modeBadge').classList.toggle('demo', config.mode === 'demo'); initMap(); beginLocation(); }
  boot().catch(error => { $('map').innerHTML = '<div class="map-fallback"><b>Map unavailable</b><span>Please check your connection and refresh.</span></div>'; notice(error.message); });
  window.addEventListener('beforeunload', () => { if (watchId && navigator.geolocation) navigator.geolocation.clearWatch(watchId); });
})();
