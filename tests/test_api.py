from fastapi.testclient import TestClient

from app import app

client = TestClient(app)


def test_health_and_dashboard_are_available():
    health = client.get("/health")
    dashboard = client.get("/api/dashboard")
    assert health.status_code == 200
    assert health.json()["storage"] == "sqlite"
    assert dashboard.status_code == 200
    assert dashboard.json()["profile"]["safety_score"] >= 0


def test_safe_telemetry_returns_positive_nudge():
    response = client.post("/api/telemetry/update", json={"speed_kmh": 35, "latitude": 12.97, "longitude": 77.59, "speed_limit_kmh": 50})
    assert response.status_code == 200
    assert response.json()["safety_nudge"]["severity"] == "safe"
    assert response.json()["safety_nudge"]["active"] is False


def test_language_preference_changes_nudge_language():
    response = client.post("/api/preferences/language", json={"language": "hi"})
    assert response.status_code == 200
    telemetry = client.get("/api/telemetry/live").json()
    assert telemetry["language"] == "hi"
    client.post("/api/preferences/language", json={"language": "en"})


def test_routes_and_challenges_have_demo_content():
    assert len(client.get("/api/routes/eco").json()["options"]) == 2
    joined = client.post("/api/challenges/phone-free/join")
    assert joined.status_code == 200 and joined.json()["joined"] is True


def test_navigation_demo_search_destination_and_road_route(monkeypatch):
    monkeypatch.setenv("YUVADRIVE_DEMO_MODE", "true")
    config = client.get("/api/navigation/config").json()
    assert config["mode"] == "demo"
    places = client.post("/api/navigation/places", json={"query": "Meenakshi"}).json()
    assert places["suggestions"][0]["place_id"] == "demo-meenakshi"
    route = client.post("/api/navigation/routes", json={"origin_latitude": 9.9252, "origin_longitude": 78.1198, "place_id": "demo-meenakshi"})
    assert route.status_code == 200
    data = route.json()
    assert len(data["routes"]) == 2
    assert len(data["routes"][0]["points"]) >= 3
    assert data["routes"][0]["estimate_source"].startswith("YuvaDrive")


def test_navigation_handles_unknown_demo_destination(monkeypatch):
    monkeypatch.setenv("YUVADRIVE_DEMO_MODE", "true")
    response = client.post("/api/navigation/places/not-a-place")
    assert response.status_code == 404
