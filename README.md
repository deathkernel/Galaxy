# 🌌 Galaxy

A public-API-powered space object explorer.

## Goal

Enter a space object, planet, star, galaxy, asteroid, comet, spacecraft, or other astronomical name and get a unified information profile.

## V1

- Search NASA/JPL public APIs
- Resolve common object names
- Return normalized object information
- Keep API credentials server-side via environment variables
- Simple browser UI
- REST API endpoint for object lookup

## Run

```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS/Linux
# source .venv/bin/activate

pip install -r requirements.txt
uvicorn app.main:app --reload
```

Open http://127.0.0.1:8000

## Environment

Copy `.env.example` to `.env`.

If a NASA API key is available, add it as `NASA_API_KEY`.
For NASA's public demo access, the app falls back to `DEMO_KEY`.

Never commit real API keys.
