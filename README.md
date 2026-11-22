# APIScope
Hybrid API discovery and reverse-engineering platform for **authorized HAR captures**.

## MVP
- HAR import and filtering of static/noise assets
- Route normalization, grouping, request counts, statuses and host inventory
- Query/header inventory, basic JSON schema inference, sensitive response-field exclusion
- Credential-like query values redacted from stored sample URLs; auth headers stored as markers only
- Passive security observations; no probing or exploitation
- OpenAPI 3.1 JSON export, generated offline pytest checks and endpoint drift comparison
- React dashboard: upload, endpoint search/filter, summary cards, details drawer, schema display, exports

## Run locally
Python 3.11+, Node 20+:
```bash
python -m venv .venv
source .venv/bin/activate
pip install -e '.[dev]'
uvicorn apiscope.main:app --reload
# another terminal
cd ui
npm install
npm run dev
```
Dashboard: http://localhost:5173 · API docs: http://localhost:8000/docs

## Docker
`docker compose up --build`

## API endpoints
- GET /health
- POST /api/v1/analyze/har (multipart `file`)
- POST /api/v1/export/openapi (scan JSON)
- POST /api/v1/generate/tests (scan JSON)
- POST /api/v1/compare (JSON with `before` and `after` scan objects)

## Tests
`python -m pytest -q`

## Limitations
No scan persistence/auth accounts, crawler, APK static analysis, scheduled scans or active security testing. Schema inference is based on observed response bodies only; verify inferred specs before use. Only analyze systems and captures you are authorized to inspect.
