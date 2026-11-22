"""APIScope REST API."""
import json
from fastapi import FastAPI,UploadFile,File,HTTPException
from fastapi.middleware.cors import CORSMiddleware
from apiscope.core.mvp_analysis import parse_har,summarize
app=FastAPI(title="APIScope",description="Passive API discovery from authorized HAR captures",version="0.2.0")
app.add_middleware(CORSMiddleware,allow_origins=["*"],allow_methods=["*"],allow_headers=["*"])
@app.get("/health")
def health():return {"status":"ok","service":"apiscope","version":"0.2.0"}
@app.post("/api/v1/analyze/har")
async def analyze_har(file:UploadFile=File(...)):
 if not (file.filename or "").lower().endswith((".har",".json")):raise HTTPException(400,"Upload a HAR or JSON file")
 try:data=json.loads(await file.read())
 except (ValueError,UnicodeDecodeError) as exc:raise HTTPException(400,"Invalid JSON file") from exc
 if not isinstance(data,dict) or not isinstance(data.get("log",{}).get("entries"),list):raise HTTPException(400,"HAR must contain log.entries")
 return summarize(parse_har(data))
@app.post("/api/v1/export/openapi")
def openapi(scan:dict):
 paths={}
 for e in scan.get("endpoints",[]):
  method=e.get("method","GET").lower();path=e.get("path","/")
  params=[{"name":q,"in":"query","required":False,"schema":{"type":"string"}} for q in e.get("query_params",[])]
  responses={}
  for code in e.get("status_codes") or ["default"]:
   r={"description":"Observed response"}
   if e.get("response_schema"):r["content"]={"application/json":{"schema":e["response_schema"]}}
   responses[str(code)]=r
  paths.setdefault(path,{})[method]={"summary":"Observed "+method.upper()+" "+path,"parameters":params,"responses":responses}
 return {"openapi":"3.1.0","info":{"title":"APIScope observed API","version":"0.2.0"},"servers":[],"paths":paths}
@app.post("/api/v1/generate/tests")
def generate(scan:dict):
 snap=json.dumps(scan,ensure_ascii=False)
 lines=['"""Generated offline API inventory tests."""','import json','SCAN=json.loads('+repr(snap)+')','def test_endpoint_count():',' assert SCAN["endpoint_count"]==len(SCAN["endpoints"])','']
 for i,e in enumerate(scan.get("endpoints",[])):
  expected=(e.get("host"),e.get("method"),e.get("path"))
  lines.extend(['def test_route_'+str(i)+'_present():',' expected='+repr(expected)," found={(x.get('host'),x.get('method'),x.get('path')) for x in SCAN['endpoints']}"," assert expected in found",''])
 return {"filename":"test_apiscope_generated.py","content":"\\n".join(lines)}
@app.post("/api/v1/compare")
def compare(body:dict):
 if not isinstance(body.get("before"),dict) or not isinstance(body.get("after"),dict):raise HTTPException(400,"Provide before and after scan objects")
 key=lambda e:(e.get("host",""),e.get("method","GET"),e.get("path",""))
 a={key(e):e for e in body["before"].get("endpoints",[])};b={key(e):e for e in body["after"].get("endpoints",[])}
 added=[b[k] for k in sorted(b.keys()-a.keys())];removed=[a[k] for k in sorted(a.keys()-b.keys())];changed=[]
 for k in sorted(a.keys()&b.keys()):
  fields=[f for f in ("status_codes","query_params","response_schema","auth_signals") if a[k].get(f)!=b[k].get(f)]
  if fields:changed.append({"endpoint":b[k]["method"]+" "+b[k]["path"],"changed_fields":fields,"before":a[k],"after":b[k]})
 return {"added":added,"removed":removed,"changed":changed,"summary":{"added":len(added),"removed":len(removed),"changed":len(changed)}}
