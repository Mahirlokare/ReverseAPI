# APIScope — Hybrid API Discovery & Reverse-Engineering Platform

APIScope is a developer/security research workbench for discovering and documenting APIs from **authorized** inputs. Its pipeline combines passive captured traffic and static source/bundle analysis, normalizes routes, infers response schemas, produces exports/tests, and provides a dashboard.

> Use only systems, apps, APKs and traffic you own or are explicitly authorized to assess. The crawler is allowlist-bounded. APIScope does not perform exploitation or vulnerability probing.

## Current implementation
- **HAR analysis:** upload validation (25 MB), static/noise exclusion, endpoint grouping, route templating for numeric/UUID/long-hex IDs, query/header inventory, response status and content type inventory.
- **Privacy handling:** query values for sensitive keys are redacted in sample URLs; auth header values are not retained; response schema inference skips sensitive-looking property names.
- **Schema inference:** infer primitive/object/array types and merge samples; fields absent from some samples become optional. Confidence is an evidence heuristic and is not benchmark accuracy.
- **JavaScript static route candidates:** upload JS/text (10 MB limit); route string extraction runs without executing uploaded code. Candidates are unverified.
- **APK static candidate extraction:** JADX adapter; no APK execution. Requires JADX installed on the backend host.
- **Allowlisted Playwright crawler:** explicitly provided hosts only, depth capped at 3, page count capped at 50 (UI defaults depth 1 and 10 pages). Requires Playwright and Chromium; local Compose installs them.
- **Passive security lint:** no auth signal, observed 5xx, sensitive-looking response-field names. Findings are observations and not proof of a vulnerability.
- **Exports:** OpenAPI 3.1 and offline pytest route inventory tests.
- **Drift comparison:** compares before/after scans to find new, removed, or changed routes and observation fields.
- **CLI:** analyze HAR files and export OpenAPI.
- **Optional persistence:** PostgreSQL scan history enabled when DATABASE_URL is set.
- **Worker configuration:** Celery + Redis config and HAR analysis task scaffold.
- **Dashboard:** HAR import, JS candidate import, crawler UI, route inventory, endpoint details, OpenAPI export and test generation.
- **Docker Compose:** API, frontend, PostgreSQL, Redis, worker and Playwright/Chromium crawler environment.

## Project structure
```
apiscope/
  main.py                 FastAPI endpoints
  cli.py                 CLI
  db.py / models.py       SQLAlchemy persistence
  storage.py              scan-history operations
  worker.py               Celery task configuration
  core/
    mvp_analysis.py       HAR parsing, schema inference, exports, drift
    static_analysis.py    JavaScript static route candidates
    apk_static.py         JADX APK adapter
    crawler.py           allowlisted bounded Playwright capture
    inference.py          inference wrappers and confidence heuristic
    security_lint.py      passive security observations
ui/                      React + TypeScript dashboard
tests/                    automated tests
```

## Quickstart (Python 3.11+)
```bash
python -m venv .venv
source .venv/bin/activate
pip install -e '.[dev]'
uvicorn apiscope.main:app --reload
```
API docs at http://localhost:8000/docs. Health at http://localhost:8000/health.

## Full local stack (Docker)
Install Docker Engine/Desktop and Compose. From the repo root:
```bash
docker compose up --build
```
- Dashboard: http://localhost:5173
- API and OpenAPI docs: http://localhost:8000/docs
- PostgreSQL: compose-internal service (credentials in compose file are for local development only)
- Redis: compose-internal
- Crawler: enabled in Compose image via Playwright Chromium

Stop services: `docker compose down`. Delete local database/cache volumes: `docker compose down -v` (destructive to local history).

## CLI
```bash
apiscope har sample.har --output scan.json
apiscope openapi scan.json --output openapi.json
```

## API routes
| Method | Path | Purpose |
|---|---|---|
| GET | / | metadata and feature list |
| GET | /health | health check |
| POST | /api/v1/analyze/har | analyze HAR upload |
| POST | /api/v1/analyze/javascript | static JS route candidates |
| POST | /api/v1/analyze/apk | APK candidate strings via JADX |
| POST | /api/v1/crawl | bounded allowlisted Playwright crawl |
| GET | /api/v1/scans | list persisted scan summaries (DATABASE_URL required) |
| GET | /api/v1/scans/{scan_id} | fetch saved scan (DATABASE_URL required) |
| POST | /api/v1/security/lint | passive observations |
| POST | /api/v1/export/openapi | OpenAPI 3.1 export |
| POST | /api/v1/generate/tests | offline pytest route tests |
| POST | /api/v1/compare | compare before/after scan objects |

## Testing
```bash
pip install -e '.[dev]'
pytest -q
python -m compileall -q apiscope tests
```
GitHub Actions runs backend tests and frontend build.

## Known gaps / roadmap
- Crawl traffic is currently returned as capture records; it is not yet transformed into the same full HAR response schema inventory.
- APK adapter currently extracts conservative route string candidates only; manifest, permissions, endpoint host reconstruction and richer code references are future work.
- JS route extraction is regex-based and intentionally conservative; false positives and misses are expected.
- The worker scaffold is present, but API routes do not yet enqueue scans asynchronously.
- Scan persistence uses SQLAlchemy create-all for prototype schema; Alembic migration workflow is still to be added.
- Authentication/accounts, multi-user tenancy, scheduled drift scans, Postman export, typed SDK generation, calibrated confidence and benchmark measurements are not yet shipped.
- Example performance figures in the project blueprint are targets/examples only; no benchmark results are claimed.

## Ethical safeguards
- Explicit allowlist is mandatory for crawler hosts.
- Crawler has depth/page caps; respect terms, robots policies and rate limits. Do not run against third-party systems without permission.
- APKs are decompiled statically; they are not executed.
- No active exploit checks, credential stuffing, fuzzing or brute force.
- Treat all results as candidates and manually validate before use.
