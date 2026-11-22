"""APIScope API server: passive capture analysis, static candidates and scan history."""
import json, tempfile, os
from pathlib import Path
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from apiscope.core.mvp_analysis import parse_har, summarize, export_openapi, compare_scans, make_tests
from apiscope.core.static_analysis import extract_routes
from apiscope.core.security_lint import lint_scan
from apiscope.storage import initialize, save_scan, list_scans, get_scan
app = FastAPI(title="APIScope",description="Hybrid API discovery for authorized inputs; passive analysis only.",version="0.4.0")
app.add_middleware(CORSMiddleware,allow_origins=["*"],allow_methods=["*"],allow_headers=["*"])
@app.on_event("startup")
def startup(): initialize()
@app.get("/")
def root(): return {"name":"APIScope","version":"0.4.0","docs":"/docs","health":"/health","features":["HAR analysis","JavaScript static analysis","APK static candidates (JADX required)","bounded crawler (Playwright extra)","scan history (DATABASE_URL)"]}
@app.get("/health")
def health(): return {"status":"ok","service":"apiscope","version":"0.4.0"}
@app.post("/api/v1/analyze/har")
async def analyze_har(file:UploadFile=File(...)):
    if not (file.filename or "").lower().endswith((".har",".json")): raise HTTPException(400,"Upload a HAR or JSON file")
    raw=await file.read()
    if len(raw)>25*1024*1024: raise HTTPException(413,"HAR upload limit is 25 MB")
    try:data=json.loads(raw)
    except (ValueError,UnicodeDecodeError) as exc: raise HTTPException(400,"Invalid JSON file") from exc
    if not isinstance(data,dict) or not isinstance(data.get("log",{}).get("entries"),list): raise HTTPException(400,"HAR must contain log.entries")
    scan=summarize(parse_har(data));scan["security_findings"]=lint_scan(scan);scan["scan_id"]=save_scan(scan,"har")
    return scan
@app.post("/api/v1/analyze/javascript")
async def analyze_javascript(file:UploadFile=File(...)):
    if not (file.filename or "").lower().endswith((".js",".txt")): raise HTTPException(400,"Upload a JavaScript bundle or text file")
    raw=await file.read()
    if len(raw)>10*1024*1024: raise HTTPException(413,"JavaScript upload limit is 10 MB")
    routes=extract_routes(raw.decode("utf-8",errors="replace"))
    return {"candidate_count":len(routes),"routes":routes,"note":"Static candidates only; verify before treating them as live endpoints."}
@app.post("/api/v1/analyze/apk")
async def analyze_apk(file:UploadFile=File(...)):
    if not (file.filename or "").lower().endswith(".apk"): raise HTTPException(400,"Upload an APK file")
    raw=await file.read()
    if len(raw)>100*1024*1024: raise HTTPException(413,"APK upload limit is 100 MB")
    from apiscope.core.apk_static import analyze_apk
    with tempfile.NamedTemporaryFile(suffix=".apk",delete=False) as tmp:
        tmp.write(raw);name=tmp.name
    try: result=analyze_apk(name)
    except RuntimeError as exc: raise HTTPException(501,str(exc)) from exc
    finally:
        try:os.unlink(name)
        except OSError:pass
    return result
@app.post("/api/v1/crawl")
async def crawl_site(body:dict):
    url=body.get("url");hosts=body.get("authorized_hosts",[])
    if not url or not isinstance(hosts,list) or not hosts: raise HTTPException(400,"Provide URL and authorized_hosts allowlist")
    from apiscope.core.crawler import crawl
    try: return await crawl(url,hosts,depth=body.get("depth",1),max_pages=body.get("max_pages",20))
    except (ValueError,RuntimeError) as exc: raise HTTPException(400,str(exc)) from exc
@app.get("/api/v1/scans")
def scans(): return {"items":list_scans()}
@app.get("/api/v1/scans/{scan_id}")
def scan_detail(scan_id:str):
    result=get_scan(scan_id)
    if result is None: raise HTTPException(404,"Scan not found or persistence is not configured")
    return result
@app.post("/api/v1/export/openapi")
def openapi(scan:dict): return export_openapi(scan)
@app.post("/api/v1/generate/tests")
def generate(scan:dict): return {"filename":"test_apiscope_generated.py","content":make_tests(scan)}
@app.post("/api/v1/security/lint")
def security_lint(scan:dict): return {"findings":lint_scan(scan)}
@app.post("/api/v1/compare")
def compare(body:dict):
    if not isinstance(body.get("before"),dict) or not isinstance(body.get("after"),dict): raise HTTPException(400,"Provide before and after scan objects")
    return compare_scans(body["before"],body["after"])
