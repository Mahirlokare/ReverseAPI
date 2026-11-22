"""Conservative JavaScript bundle route extraction (static, non-executing)."""
import re
from urllib.parse import urlparse
from apiscope.core.mvp_analysis import normalize

ROUTE = re.compile(r"""(?P<route>(?:https?://[^\s"'<>]+)?/(?:api|v[0-9]+|graphql|auth|users|accounts|orders|products|search|login|logout|session)[^\s"'<>\\]*)""", re.I)
METHOD = re.compile(r"""\b(fetch|axios\.(?:get|post|put|patch|delete)|\.get\(|\.post\(|\.put\(|\.patch\(|\.delete\()""", re.I)
def extract_routes(source: str):
    found = {}
    for match in ROUTE.finditer(source):
        raw = match.group("route").rstrip("),;")
        if raw.startswith("http"):
            parsed = urlparse(raw)
            host = parsed.netloc.lower()
            path = parsed.path or "/"
        else:
            host = ""
            path = raw.split("?")[0]
        if not path or path.startswith("//") or len(path) > 240: continue
        method = "UNKNOWN"
        nearby = source[max(0, match.start()-180):match.start()+220]
        call = METHOD.search(nearby)
        if call:
            text = call.group(0).lower()
            if "delete" in text: method = "DELETE"
            elif "patch" in text: method = "PATCH"
            elif "put" in text: method = "PUT"
            elif "post" in text: method = "POST"
            elif "get" in text: method = "GET"
        key = (host, method, normalize(path))
        found.setdefault(key, {"host": host, "method": method, "path": normalize(path), "observations": 1, "source": "javascript-static", "confidence": 0.35})
    return sorted(found.values(), key=lambda x: (x["host"], x["path"], x["method"]))
