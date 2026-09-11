# Setup

```bash
python -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
uvicorn app:app --reload
```

Open `http://127.0.0.1:8000`. The first start creates `data/yuvadrive.db`; override the location with `YUVADRIVE_DB_PATH=/path/to/demo.db`. This demo has no required API key or cloud service.

## Navigation configuration

Copy the variable names from [`.env.example`](../.env.example) into your shell or deployment-secret manager. This prototype needs no private map API key. It uses Leaflet/OpenStreetMap in the browser and configurable Nominatim-compatible search and OSRM-compatible routing providers through the backend. Set `YUVADRIVE_DEMO_MODE=true` for deterministic, clearly labelled demo data.
