#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Resolve short URLs from the missing-logo report with a real browser."""
import json
from paths import path as P
import os
import re
import sys
from urllib.parse import urlparse

HERE = os.path.dirname(os.path.abspath(__file__))
INP = P("_missing_logo_report.json")
OUT = P("_short_url_resolved.json")


def domain(url):
    host = urlparse(url).netloc.lower()
    return host[4:] if host.startswith("www.") else host


def main():
    rows = json.load(open(INP, encoding="utf-8")).get("can_try_with_network_later", [])
    targets = []
    for row in rows:
        for url in row.get("urls", []):
            if re.search(r"reurl\.cc|pse\.is|lihi|bit\.ly", url):
                targets.append((row["name"], url))
    results = {}
    from playwright.sync_api import sync_playwright
    with sync_playwright() as p:
        browser = p.chromium.launch()
        ctx = browser.new_context(ignore_https_errors=True, locale="zh-TW", user_agent="Mozilla/5.0")
        page = ctx.new_page()
        for name, url in targets:
            rec = results.setdefault(name, [])
            try:
                page.goto(url, wait_until="commit", timeout=25000)
                try:
                    page.wait_for_load_state("domcontentloaded", timeout=8000)
                except Exception:
                    pass
                page.wait_for_timeout(1800)
                final = page.url
                title = ""
                try:
                    title = page.title()
                except Exception:
                    pass
                links = page.evaluate("""() => [...document.querySelectorAll('a[href]')].slice(0,80).map(a => ({text:(a.innerText||'').trim(), href:a.href}))""")
                rec.append({"short": url, "final": final, "domain": domain(final), "title": title, "links": links[:12]})
            except Exception as e:
                rec.append({"short": url, "error": type(e).__name__, "message": str(e)[:160]})
            print(name, rec[-1].get("domain") or rec[-1].get("error"), file=sys.stderr)
        browser.close()
    json.dump(results, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(json.dumps({"short_urls": len(targets), "venues": len(results), "out": OUT}, ensure_ascii=False))


if __name__ == "__main__":
    main()
