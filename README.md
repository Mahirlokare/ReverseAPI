# APIScope — Week 1 Foundation

API discovery and reverse-engineering platform. Week 1 implements a HAR parser, noise filtering, path templating, endpoint aggregation, a FastAPI upload endpoint, and unit tests.

## Quick start
```bash
python -m venv .venv
source .venv/bin/activate
pip install -e '.[dev]'
uvicorn apiscope.main:app --reload
```
Open http://127.0.0.1:8000/docs for interactive API documentation.

## Docker
```bash
docker compose up --build
```

## API
- `GET /health` — service status
- `POST /api/v1/analyze/har` — upload HAR JSON; returns endpoint inventory grouped by host, method, and normalized path

## Tests
```bash
pytest -q
```

Only analyze traffic/assets for which you have authorization. The Week 1 parser reads HAR data; it does not execute requests against targets.
