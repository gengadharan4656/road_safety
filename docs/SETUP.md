# Setup

```bash
python -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
uvicorn app:app --reload
```

Open `http://127.0.0.1:8000`. The first start creates `data/yuvadrive.db`; override the location with `YUVADRIVE_DB_PATH=/path/to/demo.db`. This demo has no required API key or cloud service.

## Navigation credentials

Copy the variable names from [`.env.example`](../.env.example) into your shell or deployment-secret manager. A key is optional: no key starts the clearly marked Demo Mode. For real Google Maps enable **Maps JavaScript API**, **Places API (New)**, and **Routes API**, then set `GOOGLE_MAPS_API_KEY`. See the detailed [Google Maps setup](../README.md#google-maps-setup) for key restrictions and browser location requirements.
