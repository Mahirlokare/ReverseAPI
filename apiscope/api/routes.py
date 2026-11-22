"""Week 1 API routes."""
from fastapi import APIRouter, HTTPException, UploadFile, File
import json
from apiscope.core.har_parser import parse_har, summarize

router = APIRouter(prefix="/api/v1", tags=["discovery"])


@router.post("/analyze/har")
async def analyze_har(file: UploadFile = File(...)):
    """Upload a HAR JSON file and return a grouped endpoint inventory."""
    if not file.filename or not file.filename.lower().endswith((".har", ".json")):
        raise HTTPException(status_code=400, detail="Upload a .har or JSON file")
    try:
        raw = await file.read()
        payload = json.loads(raw)
        if not isinstance(payload, dict) or not isinstance(payload.get("log", {}).get("entries"), list):
            raise ValueError("Expected HAR format with log.entries array")
    except (json.JSONDecodeError, UnicodeDecodeError, ValueError) as exc:
        raise HTTPException(status_code=400, detail=f"Invalid HAR file: {exc}") from exc
    return summarize(parse_har(payload))
