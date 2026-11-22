"""APIScope MVP FastAPI service."""
import json,re
from collections import Counter
from urllib.parse import urlparse,parse_qsl,urlencode,urlunparse
from fastapi import FastAPI,UploadFile,File,HTTPException
from fastapi.middleware.cors import CORSMiddleware

app=FastAPI(title="APIScope",description="API discovery from authorized HAR captures",version="0.2.0")
app.add_middleware(CORSMiddleware,allow_origins=["http://localhost:5173","http://127.0.0.1:5173"],allow_methods=["*"],allow_headers=["*"])
SENSITIVE=re.compile(r"(password|passwd|secret|token|authorization|api[_-]?key|cookie|session)",re.I)
UUID=re.compile(r"^[0-9a-f]{8}-[0-9a-f]{4}-[1-8][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$",re.I)
HEX=re.compile(r"^[0-9a-f]{16,}$",re.I)
STATIC=(".js",".css",".map",".png",".jpg",".jpeg",".gif",".svg",".webp",".ico",".woff",".woff2",".ttf",".otf",".mp4",".webm",".pdf")

def template(path):
    return "/".join("{id}" if x.isdigit() or UUID.fullmatch(x) or HEX.fullmatch(x) else x for x in path.split("/")) or "/"
def safe_url(url):
    p=urlparse(url); qs=[(k,"REDACTED" if SENSITIVE.search(k) else v) for k,v in parse_qsl(p.query,keep_blank_values=True)]
    return urlunparse(p._replace(query=urlencode(qs)))
def infer(v):
    if v is None:return {"type":"null"}
    if isinstance(v,bool):return {"type":"boolean"}
    if isinstance(v,int):return {"type":"integer"}
    if isinstance(v,float):return {"type":"number"}
    if isinstance(v,str):return {"type":"string"}
    if isinstance(v,list):return {"type":"array","items":merge([infer(x) for x in v[:8]]) if v else {}}
    if isinstance(v,dict):
        p={k:infer(x) for k,x in v.items() if not SENSITIVE.search(k)}
        return {"type":"object","properties":p,"required":list(p)}
    return {"type":"unknown"}
def merge(ss):
    if not ss:return {}
    types=sorted(set(s.get("type","unknown") for s in ss));out={"type":types[0] if len(types)==1 else types}
    if "object" in types:
        props={}
        for s in ss:
            for k,v in s.get("properties",{}).items():props.setdefault(k,[]).append(v)
        out["properties"]={k:merge(v) for k,v in props.items()}
        out["required"]=[k for k in props if all(k in s.get("properties",{}) for s in ss)]
    if "array" in types:
        items=[s["items"] for s in ss if "items" in s]
        if items:out["items"]=merge(items)
    return out
def parse(har):
    groups={}
    for entry in har.get("log",{}).get("entries",[]):
        req=entry.get("request",{});url=req.get("url","")
        if not url:continue
        u=urlparse(url)
        if u.scheme not in ("http","https") or u.path.lower().endswith(STATIC) or u.path in ("/favicon.ico","/robots.txt"):continue
        method=req.get("method","GET").upper();path=template(u.path);key=(u.netloc.lower(),method,path)
        e=groups.setdefault(key,{"host":u.netloc.lower(),"method":method,"path":path,"observations":0,"status_codes":[],"sample_urls":[],"query_params":[],"request_headers":[],"auth_signals":[],"response_schema":{},"response_content_types":[]})
        e["observations"]+=1;status=entry.get("response",{}).get("status")
        if isinstance(status,int) and status not in e["status_codes"]:e["status_codes"].append(status)
        clean=safe_url(url)
        if clean not in e["sample_urls"] and len(e["sample_urls"])<3:e["sample_urls"].append(clean)
        e["query_params"]=sorted(set(e["query_params"])|{k for k,v in parse_qsl(u.query)})
        headers=req.get("headers",[])
        e["request_headers"]=sorted(set(e["request_headers"])|{h.get("name","") for h in headers if h.get("name")})
        for h in headers:
            n=h.get("name","").lower();v=h.get("value","").lower();marker=""
            if n=="authorization":marker="Authorization observed (redacted)"
            if n=="authorization" and v.startswith("bearer "):marker="Bearer token observed (redacted)"
            if n in ("cookie","set-cookie"):marker="Cookie/session signal observed"
            if n in ("x-api-key","api-key"):marker="API-key header observed (redacted)"
            if n in ("x-csrf-token","csrf-token"):marker="CSRF header observed"
            if marker and marker not in e["auth_signals"]:e["auth_signals"].append(marker)
        c=entry.get("response",{}).get("content",{});mime=c.get("mimeType","");body=c.get("text")
        if mime and mime.split(";")[0] not in e["response_content_types"]:e["response_content_types"].append(mime.split(";")[0])
        if body and ("json" in mime.lower() or body.lstrip().startswith(("{","["))):
            try: sample=json.loads(body);e["response_schema"]=merge([e["response_schema"],infer(sample)]) if e["response_schema"] else infer(sample)
            except (ValueError,TypeError):pass
    result=list(groups.values());result.sort(key=lambda e:(e["host"],e["path"],e["method"]))
    for e in result:e["status_codes"].sort();e["response_content_types"].sort()
    return result
def scan_result(endpoints):
    counts=Counter(e["method"] for e in endpoints)
    findings=[]
    for e in endpoints:
        label=e["method"]+" "+e["path"]
        if not e["auth_signals"] and e["path"] not in ("/","/health","/status"):
            findings.append({"severity":"info","title":"No authentication signal in capture","endpoint":label,"detail":"No marker observed; this is not proof that the endpoint is unauthenticated."})
        if any(x>=500 for x in e["status_codes"]):
            findings.append({"severity":"low","title":"Server error response observed","endpoint":label,"detail":"A 5xx response appeared in the imported capture."})
        if "{id}" in e["path"] and any(k in e["path"].lower() for k in ("user","account","order","profile")):
            findings.append({"severity":"info","title":"Identifier-based route observed","endpoint":label,"detail":"Consider reviewing object-level access control. No authorization test was performed."})
    return {"endpoint_count":len(endpoints),"total_observations":sum(e["observations"] for e in endpoints),"methods":dict(sorted(counts.items())),"hosts":sorted({e["host"] for e in endpoints}),"endpoints":endpoints,"findings":findings}
def analyze(raw,filename):
    if not filename.lower().endswith((".har",".json")):raise HTTPException(400,"Upload .har or .json")
    try:data=json.loads(raw)
    except (ValueError,UnicodeDecodeError) as exc:raise HTTPException(400,"Invalid JSON") from exc
    if not isinstance(data,dict) or not isinstance(data.get("log",{}).get("entries"),list):raise HTTPException(400,"HAR must contain log.entries")
    return scan_result(parse(data))
@app.get("/health")
def health():return {"status":"ok","service":"apiscope","version":"0.2.0"}
@app.post("/api/v1/analyze/har")
async def analyze_har(file:UploadFile=File(...)):return analyze(await file.read(),file.filename or "upload")
@app.post("/api/v1/export/openapi")
def export_openapi(scan:dict):
    paths={}
    for e in scan.get("endpoints",[]):
        method=e.get("method","GET").lower();path=e.get("path","/")
        params=[{"name":q,"in":"query","required":False,"schema":{"type":"string"}} for q in e.get("query_params",[])]
        responses={}
        for status in e.get("status_codes") or ["default"]:
            resp={"description":"Observed response"}
            if e.get("response_schema"):resp["content"]={"application/json":{"schema":e["response_schema"]}}
            responses[str(status)]=resp
        paths.setdefault(path,{})[method]={"summary":"Observed "+method.upper()+" "+path,"parameters":params,"responses":responses}
    return {"openapi":"3.1.0","info":{"title":"APIScope Observed API","version":"0.2.0","description":"Inferred from authorized capture. Validate before use."},"servers":[],"paths":paths}
@app.post("/api/v1/generate/tests")
def generate_tests(scan:dict):
    snapshot=json.dumps(scan,ensure_ascii=False)
    lines=['"""Generated offline endpoint snapshot tests."""','import json','SCAN=json.loads('+repr(snapshot)+')','def test_inventory_count():','    assert SCAN["endpoint_count"] == len(SCAN["endpoints"])','']
    for i,e in enumerate(scan.get("endpoints",[])):
        lines += ['def test_route_'+str(i)+'_present():','    expected='+repr((e.get("host"),e.get("method"),e.get("path"))),"    actual={(x.get('host'),x.get('method'),x.get('path')) for x in SCAN['endpoints']}","    assert expected in actual",'']
    return {"filename":"test_apiscope_generated.py","content":"\\n".join(lines)}
@app.post("/api/v1/compare")
def compare(body:dict):
    if not isinstance(body.get("before"),dict) or not isinstance(body.get("after"),dict):raise HTTPException(400,"Provide before and after scan objects")
    a={ (e.get("host"),e.get("method"),e.get("path")):e for e in body["before"].get("endpoints",[])}
    b={ (e.get("host"),e.get("method"),e.get("path")):e for e in body["after"].get("endpoints",[])}
    added=[b[k] for k in sorted(b.keys()-a.keys())];removed=[a[k] for k in sorted(a.keys()-b.keys())];changed=[]
    for k in sorted(a.keys()&b.keys()):
        fields=[f for f in ("status_codes","query_params","response_schema","auth_signals") if a[k].get(f)!=b[k].get(f)]
        if fields:changed.append({"endpoint":b[k]["method"]+" "+b[k]["path"],"changed_fields":fields,"before":a[k],"after":b[k]})
    return {"added":added,"removed":removed,"changed":changed,"summary":{"added":len(added),"removed":len(removed),"changed":len(changed)}}
