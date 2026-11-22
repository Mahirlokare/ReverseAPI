"""Passive API inventory analysis for authorized HAR captures."""
import json
import re
from collections import Counter
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse

SENSITIVE = re.compile(r"(password|secret|token|authorization|api[_-]?key|cookie|session)", re.I)
UUID = re.compile(r"^[0-9a-f]{8}-[0-9a-f]{4}-[1-8][0-9]{3}-[89ab][0-9]{3}-[0-9a-f]{12}$", re.I)
HEX = re.compile(r"^[a-f0-9]{16,}$", re.I)
STATIC = (".js", ".css", ".map", ".png", ".jpg", ".jpeg", ".gif", ".svg", ".webp", ".ico", ".woff", ".woff2", ".ttf", ".otf", ".mp4", ".webm", ".pdf")

def normalize(path):
    return "/" + "/".join("{id}" if x.isdigit() or UUID.fullmatch(x) or HEX.fullmatch(x) else x for x in path.strip("/").split("/") if x) if path.strip("/") else "/"

def safe_url(url):
    parsed = urlparse(url)
    pairs = [(k, "REDACTED" if SENSITIVE.search(k) else v) for k, v in parse_qsl(parsed.query, keep_blank_values=True)]
    return urlunparse(parsed._replace(query=urlencode(pairs)))

def infer(value):
    if value is None: return {"type": "null"}
    if isinstance(value, bool): return {"type": "boolean"}
    if isinstance(value, int): return {"type": "integer"}
    if isinstance(value, float): return {"type": "number"}
    if isinstance(value, str): return {"type": "string"}
    if isinstance(value, list): return {"type": "array", "items": merge_schemas([infer(x) for x in value]) if value else {}}
    if isinstance(value, dict):
        props = {k: infer(v) for k, v in value.items() if not SENSITIVE.search(k)}
        return {"type": "object", "properties": props, "required": sorted(props)}
    return {"type": "unknown"}

def merge_schemas(schemas):
    schemas = [s for s in schemas if s]
    if not schemas: return {}
    types = sorted({s.get("type", "unknown") for s in schemas})
    typ = types[0] if len(types) == 1 else types
    if typ == "object" or typ == ["object"]:
        all_props = {}
        required_sets = []
        for s in schemas:
            props = s.get("properties", {})
            required_sets.append(set(s.get("required", [])))
            for key, val in props.items(): all_props.setdefault(key, []).append(val)
        merged = {k: merge_schemas(v) for k, v in all_props.items()}
        required = sorted(set.intersection(*required_sets) if required_sets else [])
        return {"type": "object", "properties": merged, "required": required}
    if typ == "array" or typ == ["array"]:
        return {"type": "array", "items": merge_schemas([s.get("items", {}) for s in schemas])}
    return {"type": typ}

def parse_har(har):
    grouped = {}
    for row in har.get("log", {}).get("entries", []):
        req = row.get("request", {}); url = req.get("url", "")
        if not url: continue
        u = urlparse(url)
        if u.scheme not in ("http", "https") or u.path.lower().endswith(STATIC) or u.path in ("/favicon.ico", "/robots.txt"): continue
        method = req.get("method", "GET").upper(); path = normalize(u.path); key = (u.netloc.lower(), method, path)
        ep = grouped.setdefault(key, {"host": u.netloc.lower(), "method": method, "path": path, "observations": 0, "status_codes": [], "sample_urls": [], "query_params": [], "request_headers": [], "auth_signals": [], "response_schemas": [], "response_schema": {}, "response_content_types": [], "confidence": 0})
        ep["observations"] += 1
        status = row.get("response", {}).get("status")
        if isinstance(status, int) and status not in ep["status_codes"]: ep["status_codes"].append(status)
        sample = safe_url(url)
        if sample not in ep["sample_urls"] and len(ep["sample_urls"]) < 3: ep["sample_urls"].append(sample)
        ep["query_params"] = sorted(set(ep["query_params"]) | {k for k, _ in parse_qsl(u.query)})
        headers = req.get("headers", [])
        ep["request_headers"] = sorted(set(ep["request_headers"]) | {h.get("name", "") for h in headers if h.get("name")})
        for h in headers:
            name = h.get("name", "").lower(); val = h.get("value", "").lower(); signal = ""
            if name == "authorization": signal = "Bearer token observed (redacted)" if val.startswith("bearer ") else "Authorization observed (redacted)"
            elif name in ("cookie", "set-cookie"): signal = "Cookie/session marker"
            elif name in ("x-api-key", "api-key"): signal = "API-key marker (redacted)"
            if signal and signal not in ep["auth_signals"]: ep["auth_signals"].append(signal)
        content = row.get("response", {}).get("content", {}); mime = content.get("mimeType", ""); body = content.get("text")
        if mime and mime.split(";")[0] not in ep["response_content_types"]: ep["response_content_types"].append(mime.split(";")[0])
        if body and ("json" in mime.lower() or body.lstrip().startswith(("{", "["))):
            try: ep["response_schemas"].append(infer(json.loads(body)))
            except (ValueError, TypeError): pass
    result = sorted(grouped.values(), key=lambda x: (x["host"], x["path"], x["method"]))
    for ep in result:
        ep["status_codes"].sort()
        ep["response_schema"] = merge_schemas(ep.pop("response_schemas"))
        ep["confidence"] = min(0.99, round(0.45 + min(ep["observations"], 10) * 0.05, 2))
    return result

def summarize(endpoints):
    methods = Counter(e["method"] for e in endpoints); findings = []
    for e in endpoints:
        route = e["method"] + " " + e["path"]
        if not e["auth_signals"] and e["path"] not in ("/", "/health", "/status"):
            findings.append({"severity": "info", "title": "No auth signal in capture", "endpoint": route, "detail": "Not proof of an unauthenticated endpoint."})
        if any(s >= 500 for s in e["status_codes"]):
            findings.append({"severity": "low", "title": "Server error observed", "endpoint": route, "detail": "A 5xx response was present in the HAR."})
    return {"endpoint_count": len(endpoints), "total_observations": sum(e["observations"] for e in endpoints), "methods": dict(sorted(methods.items())), "hosts": sorted({e["host"] for e in endpoints}), "endpoints": endpoints, "findings": findings}

def export_openapi(scan):
    paths = {}
    for e in scan.get("endpoints", []):
        method = e.get("method", "GET").lower(); path = e.get("path", "/")
        params = [{"name": name, "in": "query", "required": False, "schema": {"type": "string"}} for name in e.get("query_params", [])]
        responses = {}
        for code in e.get("status_codes") or ["default"]:
            response = {"description": "Observed response"}
            if e.get("response_schema"): response["content"] = {"application/json": {"schema": e["response_schema"]}}
            responses[str(code)] = response
        paths.setdefault(path, {})[method] = {"summary": "Observed " + method.upper() + " " + path, "parameters": params, "responses": responses}
    return {"openapi": "3.1.0", "info": {"title": "APIScope observed API", "version": "0.1.0"}, "servers": [], "paths": paths}

def compare_scans(before, after):
    key = lambda e: (e.get("host", ""), e.get("method", "GET"), e.get("path", "/"))
    a = {key(e): e for e in before.get("endpoints", [])}; b = {key(e): e for e in after.get("endpoints", [])}
    added = [b[k] for k in sorted(b.keys() - a.keys())]; removed = [a[k] for k in sorted(a.keys() - b.keys())]; changed = []
    for k in sorted(a.keys() & b.keys()):
        fields = [f for f in ("status_codes", "query_params", "response_schema", "auth_signals") if a[k].get(f) != b[k].get(f)]
        if fields: changed.append({"endpoint": b[k]["method"] + " " + b[k]["path"], "changed_fields": fields, "before": a[k], "after": b[k]})
    return {"added": added, "removed": removed, "changed": changed, "summary": {"added": len(added), "removed": len(removed), "changed": len(changed)}}

def make_tests(scan):
    snapshot = json.dumps(scan, ensure_ascii=False)
    lines = ['"""Generated offline API inventory tests."""', "import json", "SCAN=json.loads(" + repr(snapshot) + ")", "def test_endpoint_count():", ' assert SCAN["endpoint_count"]==len(SCAN["endpoints"])', ""]
    for i, e in enumerate(scan.get("endpoints", [])):
        expected = (e.get("host"), e.get("method"), e.get("path"))
        lines += ["def test_route_" + str(i) + "_exists():", " expected=" + repr(expected), " found={(x.get('host'),x.get('method'),x.get('path')) for x in SCAN['endpoints']}", " assert expected in found", ""]
    return "\n".join(lines)
