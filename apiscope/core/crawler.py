"""Bounded Playwright crawler restricted to explicit authorized hosts."""
from urllib.parse import urlparse
from collections import deque
async def crawl(url,authorized_hosts,depth=1,max_pages=20,timeout_ms=12000):
    try: from playwright.async_api import async_playwright
    except ImportError as exc: raise RuntimeError("Install Playwright: pip install playwright; then playwright install chromium") from exc
    allow={h.lower().strip() for h in authorized_hosts if h.strip()}
    start=urlparse(url)
    if start.hostname not in allow: raise ValueError("Start host must be in the explicit authorized-host allowlist")
    depth=max(0,min(int(depth),3));max_pages=max(1,min(int(max_pages),50))
    visited=set();captured=[];queue=deque([(url,0)])
    async with async_playwright() as p:
        browser=await p.chromium.launch(headless=True)
        context=await browser.new_context()
        page=await context.new_page()
        async def record(req):
            parsed=urlparse(req.url)
            if parsed.hostname in allow and parsed.scheme in ("http","https"):
                captured.append({"method":req.method,"url":req.url,"resource_type":req.resource_type,"status":None,"auth_markers":[]})
                for header in req.headers:
                    name=header.lower()
                    if name=="authorization":captured[-1]["auth_markers"].append("Authorization observed (value not stored)")
                    if name in ("cookie","x-api-key"):captured[-1]["auth_markers"].append(name+" marker (value not stored)")
        async def record_response(resp):
            req=resp.request
            for item in reversed(captured):
                if item["url"]==req.url and item["method"]==req.method and item["status"] is None:
                    item["status"]=resp.status;break
        page.on("request",record);page.on("response",record_response)
        while queue and len(visited)<max_pages:
            target,d=queue.popleft()
            if target in visited:continue
            parsed=urlparse(target)
            if parsed.hostname not in allow or parsed.scheme not in ("http","https"):continue
            visited.add(target)
            try:
                await page.goto(target,wait_until="domcontentloaded",timeout=timeout_ms)
                if d<depth:
                    links=await page.locator("a[href]").evaluate_all("(els)=>els.map(e=>e.href)")
                    for link in links:
                        lp=urlparse(link)
                        if lp.hostname in allow and lp.scheme in ("http","https") and link not in visited:queue.append((link,d+1))
            except Exception:continue
        await browser.close()
    merged={}
    for item in captured:
        key=(item["method"],item["url"])
        if key not in merged:merged[key]={**item,"observations":0}
        merged[key]["observations"]+=1
        if item["status"] is not None:merged[key]["status"]=item["status"]
        merged[key]["auth_markers"]=sorted(set(merged[key]["auth_markers"]+item["auth_markers"]))
    return {"pages_visited":len(visited),"requests":list(merged.values()),"scope_hosts":sorted(allow)}
