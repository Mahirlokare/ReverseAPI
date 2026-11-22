# APIScope
Hybrid API discovery and reverse-engineering for authorized HAR captures.

## Features
- HAR upload and parsing; static/noise filtering
- Route templating and grouping by host/method/path
- Query/header inventory and status observations
- Basic response JSON schema inference (sensitive field names omitted)
- Auth marker observations with values redacted
- Passive security observations only (no target requests/exploitation)
- OpenAPI 3.1 export, offline pytest generator, scan comparison API
- React dashboard with endpoint inventory, search, method filtering, details and exports

## Run locally
Python 3.11+, Node 20+:
\`\`\`bash
python -m venv .venv && source .venv/bin/activate
pip install -e '.[dev]'
uvicorn apiscope.main:app --reload
# second terminal
cd ui && npm install && npm run dev
\`\`\`
UI at http://localhost:5173, API docs at http://localhost:8000/docs.

## Docker
\`docker compose up --build\`

## API endpoints
- GET /health
- POST /api/v1/analyze/har (multipart field \`file\`)
- POST /api/v1/export/openapi (scan JSON)
- POST /api/v1/generate/tests (scan JSON)
- POST /api/v1/compare (JSON body: before, after)

## Tests
\`python -m pytest -q\`

## Limitations
MVP has no persistence, user accounts, crawler, APK analysis, scheduled scans or active security testing. Inferred schemas are based only on captured response samples. Treat HARs as sensitive and only analyze captures you are authorized to inspect.
