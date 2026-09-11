# Setup

```bash
python -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
uvicorn app:app --reload
```

Open `http://127.0.0.1:8000`. The first start creates `data/yuvadrive.db`; override the location with `YUVADRIVE_DB_PATH=/path/to/demo.db`. This demo has no required API key or cloud service.
