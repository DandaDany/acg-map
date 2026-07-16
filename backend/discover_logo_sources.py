#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Find official-site / Facebook candidates for venues that still have no logo.

This script does not modify project data. It writes _logo_source_candidates.json
for manual review, then confirmed entries can be added to venue_logos.json or
fb_pages.json.
"""
import json, os, re, sys
from paths import path as P
from urllib.parse import quote, urlparse, parse_qs, unquote

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = P("_logo_source_candidates.json")

BAD_DOMAINS = (
    "google.", "bing.", "yahoo.", "brave.com", "facebook.com/search",
    "wikipedia.org", "tripadvisor.", "klook.", "kkday.", "booking.",
    "agoda.", "youtube.", "instagram.com/explore", "threads.net",
)

def clean_url(url):
    if not url:
        return ""
    if "r.search.yahoo.com" in url:
        qs = parse_qs(urlparse(url).query)
        if "RU" in qs:
            return unquote(qs["RU"][0])
    return url

def domain(url):
    try:
        h = urlparse(url).netloc.lower()
        return h[4:] if h.startswith("www.") else h
    except Exception:
        return ""

def good_url(url):
    d = domain(url)
    return d and not any(x in url.lower() or x in d for x in BAD_DOMAINS)

def missing_names(limit=8):
    data = json.load(open(P("venues.json"), encoding="utf-8"))
    rows = [v for v in data.get("venues", []) if not v.get("logo")]
    skip = re.compile(r"威秀|LaLaport|MITSUI|OUTLET|百貨|夢時代|京站|遠百|裕隆城|中友|統一時代|海洋公園|棒球場|花火節|氣球|café|咖啡|高雄駅|未具名|第1、2展覽廳|中正紀念堂1展廳|鹽埕區$|澎湖$|台東$|花海廣場", re.I)
    rows = [v for v in rows if not skip.search(v.get("name", ""))]
    rows.sort(key=lambda v: (-len(v.get("ex", [])), v.get("city", ""), v.get("name", "")))
    return [v["name"] for v in rows[:limit]]

def search_page(page, url):
    page.goto(url, wait_until="domcontentloaded", timeout=25000)
    page.wait_for_timeout(700)
    return page.evaluate(r"""
        () => [...document.querySelectorAll('a')].map(a => ({
          text: (a.innerText || '').trim(),
          href: a.href || ''
        })).filter(x => x.href).slice(0, 120)
    """)

def main():
    names = sys.argv[1:] or missing_names()
    out = {}
    from playwright.sync_api import sync_playwright
    with sync_playwright() as p:
        browser = p.chromium.launch()
        ctx = browser.new_context(locale="zh-TW", user_agent="Mozilla/5.0")
        page = ctx.new_page()
        for name in names:
            candidates = []
            queries = [f'"{name}" 官方網站', f'"{name}" Facebook']
            for q in queries:
                urls = ["https://tw.search.yahoo.com/search?p=" + quote(q)]
                for url in urls:
                    try:
                        for row in search_page(page, url):
                            href = clean_url(row.get("href", ""))
                            if not good_url(href):
                                continue
                            candidates.append({
                                "query": q,
                                "title": re.sub(r"\s+", " ", row.get("text", ""))[:160],
                                "url": href,
                                "domain": domain(href),
                                "facebook": "facebook.com" in href,
                            })
                    except Exception as e:
                        candidates.append({"query": q, "error": type(e).__name__, "message": str(e)[:120]})
            seen = set()
            deduped = []
            for c in candidates:
                key = c.get("url") or c.get("message")
                if key in seen:
                    continue
                seen.add(key)
                deduped.append(c)
            out[name] = deduped[:12]
        browser.close()
    json.dump(out, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(json.dumps({"venues": len(out), "out": OUT}, ensure_ascii=False))

if __name__ == "__main__":
    main()
