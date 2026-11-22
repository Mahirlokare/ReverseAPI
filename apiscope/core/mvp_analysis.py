"""APIScope passive HAR analyzer."""
import json,re
from collections import Counter
from urllib.parse import urlparse,parse_qsl,urlencode,urlunparse
SENSITIVE=re.compile(r"(password|secret|token|authorization|api[_-]?key|cookie|session)",re.I)
UUID=re.compile(r"^[0-9a-f]{8}-[0-9a-f]{4}-[1-8][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$",re.I)
HEX=re.compile(r"^[a-f0-9]{16,}$",re.I)
STATIC=(".js",".css",".map",".png",".jpg",".jpeg",".gif",".svg",".webp",".ico",".woff",".woff2",".ttf",".otf",".mp4",".webm",".pdf")
def normalize(path):
 return "/".join("{id}" if x.isdigit() or UUID.fullmatch(x) or HEX.fullmatch(x) else x for x in path.split("/")) or "/"
def safe_url(url):
 p=urlparse(url);q=[(k,"REDACTED" if SENSITIVE.search(k) else v) for k,v in parse_qsl(p.query,keep_blank_values=True)]
 return urlunparse(p._replace(query=urlencode(q)))
def infer(v):
 if v is None:return {"type":"null"}
 if isinstance(v,bool):return {"type":"boolean"}
 if isinstance(v,int):return {"type":"integer"}
 if isinstance(v,float):return {"type":"number"}
 if isinstance(v,str):return {"type":"string"}
 if isinstance(v,list):return {"type":"array","items":infer(v[0]) if v else {}}
 if isinstance(v,dict):
  props={k:infer(x) for k,x in v.items() if not SENSITIVE.search(k)}
  return {"type":"object","properties":props,"required":list(props)}
 return {"type":"unknown"}
def parse_har(har):
 groups={}
 for row in har.get("log",{}).get("entries",[]):
  req=row.get("request",{});url=req.get("url","")
  if not url:continue
  u=urlparse(url)
  if u.scheme not in ("http","https") or u.path.lower().endswith(STATIC) or u.path in ("/favicon.ico","/robots.txt"):continue
  method=req.get("method","GET").upper();path=normalize(u.path);key=(u.netloc.lower(),method,path)
  ep=groups.setdefault(key,{"host":u.netloc.lower(),"method":method,"path":path,"observations":0,"status_codes":[],"sample_urls":[],"query_params":[],"request_headers":[],"auth_signals":[],"response_schema":{},"response_content_types":[]})
  ep["observations"]+=1;status=row.get("response",{}).get("status")
  if isinstance(status,int) and status not in ep["status_codes"]:ep["status_codes"].append(status)
  sample=safe_url(url)
  if sample not in ep["sample_urls"] and len(ep["sample_urls"])<3:ep["sample_urls"].append(sample)
  ep["query_params"]=sorted(set(ep["query_params"])|{k for k,v in parse_qsl(u.query)})
  headers=req.get("headers",[]);ep["request_headers"]=sorted(set(ep["request_headers"])|{h.get("name","") for h in headers if h.get("name")})
  for h in headers:
   n=h.get("name","").lower();v=h.get("value","").lower();marker=""
   if n=="authorization":marker="Authorization observed (redacted)"
   if n=="authorization" and v.startswith("bearer "):marker="Bearer token observed (redacted)"
   if n in ("cookie","set-cookie"):marker="Cookie/session marker"
   if n in ("x-api-key","api-key"):marker="API-key marker (redacted)"
   if marker and marker not in ep["auth_signals"]:ep["auth_signals"].append(marker)
  c=row.get("response",{}).get("content",{});mime=c.get("mimeType","");body=c.get("text")
  if mime and mime.split(";")[0] not in ep["response_content_types"]:ep["response_content_types"].append(mime.split(";")[0])
  if body and ("json" in mime.lower() or body.lstrip().startswith(("{","["))):
   try:ep["response_schema"]=infer(json.loads(body))
   except (ValueError,TypeError):pass
 result=sorted(groups.values(),key=lambda x:(x["host"],x["path"],x["method"]))
 for e in result:e["status_codes"].sort()
 return result
def summarize(endpoints):
 methods=Counter(e["method"] for e in endpoints)
 notes=[]
 for e in endpoints:
  ep=e["method"]+" "+e["path"]
  if not e["auth_signals"] and e["path"] not in ("/","/health","/status"):notes.append({"severity":"info","title":"No auth signal in capture","endpoint":ep,"detail":"Not proof of an unauthenticated endpoint."})
  if any(x>=500 for x in e["status_codes"]):notes.append({"severity":"low","title":"Server error observed","endpoint":ep,"detail":"A 5xx response was present in the HAR."})
 return {"endpoint_count":len(endpoints),"total_observations":sum(e["observations"] for e in endpoints),"methods":dict(sorted(methods.items())),"hosts":sorted({e["host"] for e in endpoints}),"endpoints":endpoints,"findings":notes}
