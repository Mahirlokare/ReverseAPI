# APIScope

**APIScope** is a hybrid API discovery and reverse-engineering workbench for authorized traffic captures. It is being developed toward the project blueprint: capture and static discovery, normalized endpoint inventory, schema inference, security observations, API exports, test generation and version drift.

## Implemented in this repository today
- HAR/JSON import with validation and a 25 MB upload limit
- Static/noise filtering and route normalization (numeric IDs, UUIDs, long hex IDs)
- Endpoint grouping by host, HTTP method and normalized route
- Query parameter and request header inventory
- Authentication signals detected from headers (values are not stored)
- Query-string secret redaction in sample URLs
- Response JSON schema inference and merging across observations (common fields required, observed-only optional fields)
- Per-endpoint observational confidence indicator (heuristic, not a measured accuracy score)
- Passive observations for missing auth signals and observed 5xx responses
- OpenAPI 3.1 export
- Offline pytest inventory generator
- Compare two inventories to report added, removed and changed routes/fields
- React + TypeScript dashboard with HAR upload, endpoint search/filter, endpoint details and export controls

## Planned roadmap (not yet implemented)
- Playwright website crawler with explicit authorization/consent and bounded crawl settings
- APK static analysis via jadx/apktool
- JavaScript bundle route extraction
- Persistent scan history (PostgreSQL)
- Background processing (Redis + Celery/RQ)
- Postman export, typed client generator, richer security rules
- Confidence calibration and benchmark harness with measured precision/recall
- CLI and richer dashboard pages

Do not treat roadmap items or example metrics in the project blueprint as implemented. No active probing or exploitation is performed.

## Quickstart (Python 3.11+)
```bash
python -m venv .venv
source .venv/bin/activate
pip install -e '.[dev]'
uvicorn apiscope.main:app --reload
```
API docs: http://localhost:8000/docs · health: http://localhost:8000/health

## Frontend (Node 20+)
```bash
cd ui
npm install
npm run dev
```
Dashboard: http://localhost:5173. Configure the API origin with `VITE_API_BASE` when running separately.

## Docker
```bash
docker compose up --build
```

## API
- `GET /` service metadata
- `GET /health` health status
- `POST /api/v1/analyze/har` multipart `file` upload
- `POST /api/v1/export/openapi` scan JSON body
- `POST /api/v1/generate/tests` scan JSON body
- `POST /api/v1/compare` JSON body with `before` and `after` scan objects

## Tests
```bash
python -m pytest -q
python -m compileall -q apiscope tests
```
GitHub Actions runs backend tests and frontend build on push/PR.

## Privacy and responsible use
Analyze only applications and traffic you have permission to inspect. APIScope is passive: it does not exploit endpoints. Credential-like query parameters are redacted from sample URLs; sensitive response fields are excluded from inferred schemas. Verify exported schemas before relying on them.
