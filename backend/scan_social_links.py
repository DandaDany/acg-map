#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import json, os, re, sys
from paths import path as P
from urllib.parse import urlparse

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = P("_social_scan.json")

def clean_fb(url):
    if not url or "facebook.com" not in url:
        return ""
    url = url.replace("https://l.facebook.com/l.php?u=", "")
    url = url.split("?")[0].split("#")[0].rstrip("/")
    if re.search(r"/(sharer|share|plugins|dialog|login|recover|tr|events)(/|$)", url):
        return ""
    return url

def domains_from_current_fallback():
    data = json.load(open(P("venues.json"), encoding="utf-8"))
    domains = []
    for v in data.get("venues", []):
        logo = v.get("logo", "")
        if "icons.duckduckgo.com" not in logo:
            continue
        dom = logo.rsplit("/", 1)[-1].removesuffix(".ico")
        if dom not in domains:
            domains.append(dom)
    return domains

def main():
    domains = sys.argv[1:] or domains_from_current_fallback()
    from playwright.sync_api import sync_playwright
    results = {}
    with sync_playwright() as p:
        browser = p.chromium.launch()
        ctx = browser.new_context(
            viewport={"width": 1366, "height": 900},
            ignore_https_errors=True,
            locale="zh-TW",
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124 Safari/537.36",
        )
        page = ctx.new_page()
        for dom in domains:
            hosts = [dom] if dom.startswith("www.") else ["www." + dom, dom]
            result = {"loaded_url": "", "errors": [], "facebook": [], "images": []}
            for host in hosts:
                try:
                    page.goto("https://" + host, wait_until="commit", timeout=25000)
                    try:
                        page.wait_for_load_state("domcontentloaded", timeout=7000)
                    except Exception:
                        pass
                    page.wait_for_timeout(2200)
                    result["loaded_url"] = page.url
                    break
                except Exception as e:
                    result["errors"].append({"url": "https://" + host, "error": type(e).__name__, "message": str(e)[:180]})
            if result["loaded_url"]:
                data = page.evaluate(r"""
                    () => ({
                      facebook: [...document.querySelectorAll('a[href*="facebook.com"], a[href*="fb.com"]')]
                        .map(a => ({href:a.href, text:(a.innerText||a.getAttribute('aria-label')||a.title||'').trim()})),
                      images: [...document.querySelectorAll('meta[property="og:image"], meta[name="twitter:image"], link[rel*="icon"]')]
                        .map(x => x.content || x.href || '').filter(Boolean)
                    })
                """)
                result["facebook"] = [x for x in data["facebook"] if clean_fb(x.get("href"))]
                result["images"] = data["images"]
            results[dom] = result
        browser.close()
    json.dump(results, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(json.dumps(results, ensure_ascii=False, indent=1))

if __name__ == "__main__":
    main()
