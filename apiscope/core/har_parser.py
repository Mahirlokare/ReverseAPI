"""Parse HAR 1.2 files into normalized endpoint observations."""
from __future__ import annotations
from collections import Counter
from dataclasses import dataclass
from typing import Any
from urllib.parse import urlparse
import re

_UUID_RE = re.compile(r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[1-8][0-9a-fA-F]{3}-[89abAB][0-9a-fA-F]{3}-[0-9a-fA-F]{12}$")
_INT_RE = re.compile(r"^\d+$")
_HEX_RE = re.compile(r"^[0-9a-fA-F]{16,}$")
STATIC_EXTENSIONS = {".js", ".css", ".map", ".png", ".jpg", ".jpeg", ".gif", ".svg", ".webp", ".ico", ".woff", ".woff2", ".ttf", ".otf", ".mp4", ".webm", ".pdf"}
NOISE_PATHS = {"/favicon.ico", "/robots.txt"}

@dataclass(frozen=True)
class EndpointObservation:
    method: str
    path_template: str
    host: str
    status_codes: tuple[int, ...]
    observations: int
    sample_urls: tuple[str, ...]

def _is_noise(url: str) -> bool:
    parsed = urlparse(url)
    path = parsed.path.lower()
    if path in NOISE_PATHS:
        return True
    return any(path.endswith(ext) for ext in STATIC_EXTENSIONS)

def normalize_path(path: str) -> str:
    """Replace likely dynamic path segments (numeric IDs, UUIDs, long hex IDs) with {id}."""
    normalized = []
    for segment in path.split("/"):
        if _INT_RE.match(segment) or _UUID_RE.match(segment) or _HEX_RE.match(segment):
            normalized.append("{id}")
        else:
            normalized.append(segment)
    return "/".join(normalized) or "/"

def parse_har(data: dict[str, Any], include_static: bool = False) -> list[EndpointObservation]:
    """Parse HAR entries and aggregate by method, host and normalized path."""
    entries = data.get("log", {}).get("entries", [])
    grouped: dict[tuple[str, str, str], dict[str, Any]] = {}
    for entry in entries:
        request = entry.get("request", {})
        url = request.get("url", "")
        if not url:
            continue
        parsed = urlparse(url)
        if parsed.scheme not in {"http", "https"}:
            continue
        if not include_static and _is_noise(url):
            continue
        method = str(request.get("method", "GET")).upper()
        path_template = normalize_path(parsed.path)
        key = (parsed.netloc.lower(), method, path_template)
        status = entry.get("response", {}).get("status")
        bucket = grouped.setdefault(key, {"statuses": [], "urls": [], "count": 0})
        bucket["count"] += 1
        if isinstance(status, int):
            bucket["statuses"].append(status)
        if url not in bucket["urls"] and len(bucket["urls"]) < 3:
            bucket["urls"].append(url)
    results = [EndpointObservation(method, path, host, tuple(sorted(set(bucket["statuses")))), bucket["count"], tuple(bucket["urls"])) for (host, method, path), bucket in grouped.items()]
    results.sort(key=lambda x: (x.host, x.path_template, x.method))
    return results

def summarize(observations: list[EndpointObservation]) -> dict[str, Any]:
    method_counts = Counter(o.method for o in observations)
    return {"endpoint_count": len(observations), "total_observations": sum(o.observations for o in observations), "methods": dict(sorted(method_counts.items())), "endpoints": [{"host": o.host, "method": o.method, "path": o.path_template, "observations": o.observations, "status_codes": list(o.status_codes), "sample_urls": list(o.sample_urls)} for o in observations]}
