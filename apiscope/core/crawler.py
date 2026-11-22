"""Bounded Playwright crawler for explicitly authorized websites."""
from urllib.parse import urljoin,urlparse
from collections import deque
async def crawl(url,authorized_hosts,depth=1,max_pages=20,timeout_ms=12000):
    try: from playwright.async_api import async_playwright
    except ImportError as exc: raise RuntimeError("Install APIScope capture extra: pip install -e '.[capture'") from exc
    allowed={h.lower() for h in authorized_hosts}; start=urlparse(url)
    if start.hostname not in allowed: raise ValueError("Start host must be in the explicit authorized-host allowlist")
    depth=max(0,min(int(depth),3)); max_pages=max(1,min(int(max_pages),50))
    visited=set(); captured=[]; queue=deque([(url,0)])
    async with async_playwright() as p:
        browser=await p.chromium.launch(headless=True)
        context=await browser.new_context()
        page=await context.new_page()
        async def record(req):
            parsed=urlparse(req.url)
            if parsed.hostname in allowed and parsed.scheme in ("http","https"):
                captured.append({"method":req.method,"url":req.url,"resource_type":req.resource_type})
        page.on("request",record)
        while queue and len(visited)<max_pages:
            target,d=queue.popleft()
            if target in visited: continue
            parsed=urlparse(target)
            if parsed.hostname not in allowed: continue
            visited.add(target)
            try:
                await page.goto(target,wait_until="domcontentloaded",timeout=timeout_ms)
                if d<depth:
                    links=await page.locator("a[href]").evaluate_all("(els)=>els.map(e=>e.href)")
                    for link in links:
                        lp=urlparse(link)
                        if lp.hostname in allowed and lp.scheme in ("http","https") and link not in visited: queue.append((link,d+1))
            except Exception: continue
        await browser.close()
    # Deduplicate observations by method and URL, keeping capture counts.
    merged={}
    for item in captured:
        key=(item["method"],item["url"])
        merged.setdefault(key,{**item,"observations":0})["observations"]+=1
    return {"pages_visited":len(visited),"requests":list(merged.values()),"scope_hosts":sorted(allowed)}
