"""APIScope API server for authorized, passive capture analysis."""
import json
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from apiscope.core.mvp_analysis import parse_har, summarize, export_openapi, compare_scans, make_tests
from apiscope.core.static_analysis import extract_routes

app = FastAPI(title="APIScope", description="Passive API discovery from authorized HAR captures", version="0.3.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

@app.get("/")
def root():
    return {"name": "APIScope", "version": "0.3.0", "docs": "/docs", "health": "/health"}

@app.get("/health")
def health():
    return {"status": "ok", "service": "apiscope", "version": "0.3.0"}

@app.post("/api/v1/analyze/har")
async def analyze_har(file: UploadFile = File(...)):
    if not (file.filename or "").lower().endswith((".har", ".json")):
        raise HTTPException(400, "Upload a HAR or JSON file")
    raw = await file.read()
    if len(raw) > 25 * 1024 * 1024:
        raise HTTPException(413, "HAR upload limit is 25 MB")
    try:
        data = json.loads(raw)
    except (ValueError, UnicodeDecodeError) as exc:
        raise HTTPException(400, "Invalid JSON file") from exc
    if not isinstance(data, dict) or not isinstance(data.get("log", {}).get("entries"), list):
        raise HTTPException(400, "HAR must contain log.entries")
    return summarize(parse_har(data))

@app.post("/api/v1/export/openapi")
def openapi(scan: dict):
    return export_openapi(scan)

@app.post("/api/v1/generate/tests")
def generate(scan: dict):
    return {"filename": "test_apiscope_generated.py", "content": make_tests(scan)}


@app.post("/api/v1/analyze/javascript")
async def analyze_javascript(file: UploadFile = File(...)):
    if not (file.filename or "").lower().endswith((".js", ".txt")):
        raise HTTPException(400, "Upload a JavaScript bundle or text file")
    raw = await file.read()
    if len(raw) > 10 * 1024 * 1024:
        raise HTTPException(413, "JavaScript upload limit is 10 MB")
    try:
        source = raw.decode("utf-8", errors="replace")
    except Exception as exc:
        raise HTTPException(400, "Could not decode source file") from exc
    routes = extract_routes(source)
    return {"candidate_count": len(routes), "routes": routes, "note": "Static candidates only; verify before treating them as live endpoints."}

@app.post("/api/v1/compare")
def compare(body: dict):
    if not isinstance(body.get("before"), dict) or not isinstance(body.get("after"), dict):
        raise HTTPException(400, "Provide before and after scan objects")
    return compare_scans(body["before"], body["after"])
