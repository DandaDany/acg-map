#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Collect fallback venue logos from 非池中藝術網 museum listings.

This is intentionally a fallback source:
  1. Match only venues already present in venues.json.
  2. Skip venues that already have a local official logo in logo_map.json.
  3. Download images locally so the frontend does not hotlink third-party CDN URLs.

Usage:
  /Users/daniel0522/miniforge3/bin/python3 collect_artemperor_museums.py
"""
import json, os, re
from paths import path as P
from urllib.parse import urlparse

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = P("artemperor_logos.json")
LOGODIR = P("logos", "artemperor")
os.makedirs(LOGODIR, exist_ok=True)

BASE = "https://artemperor.tw/museums?page={page}"
PAGES = 8

def norm(s):
    return re.sub(r"\s+", "", (s or "").replace("臺", "台").strip())

def slug(s):
    s = norm(s).lower()
    s = re.sub(r"[^a-z0-9\u4e00-\u9fff]+", "_", s)
    return s.strip("_")[:80] or "venue"

def ext_of(url, ctype=""):
    path = urlparse(url).path
    m = re.search(r"\.(svg|png|jpe?g|webp|ico)$", path, re.I)
    if m:
        return "." + m.group(1).lower().replace("jpeg", "jpg")
    if "svg" in ctype:
        return ".svg"
    if "png" in ctype:
        return ".png"
    if "webp" in ctype:
        return ".webp"
    return ".jpg"

def venue_names_without_local_official_logo():
    data = json.load(open(P("venues.json"), encoding="utf-8"))
    lmap = json.load(open(P("venue_logos.json"), encoding="utf-8")).get("map", [])
    logo_map_path = P("logo_map.json")
    logo_map = json.load(open(logo_map_path, encoding="utf-8")) if os.path.exists(logo_map_path) else {}
    out = []
    for v in data.get("venues", []):
        name = v.get("name", "")
        has_local = False
        for kw, dom in lmap:
            if kw and kw in name and dom in logo_map:
                has_local = True
                break
        if not has_local:
            out.append(name)
    return out

def match_venue(source_name, candidates):
    sn = norm(source_name)
    if not sn:
        return ""
    by_norm = {norm(v): v for v in candidates}
    if sn in by_norm:
        return by_norm[sn]
    for vn, original in by_norm.items():
        if len(vn) >= 5 and (vn in sn or sn in vn):
            return original
    return ""

def scrape():
    from playwright.sync_api import sync_playwright
    rows = []
    with sync_playwright() as p:
        browser = p.chromium.launch()
        ctx = browser.new_context(
            viewport={"width": 1366, "height": 900},
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124 Safari/537.36",
        )
        page = ctx.new_page()
        for i in range(1, PAGES + 1):
            page.goto(BASE.format(page=i), wait_until="domcontentloaded", timeout=30000)
            page.wait_for_timeout(1500)
            rows.extend(page.evaluate(r"""
                () => [...document.querySelectorAll('a.gallery_box')].map(a => ({
                    name: (a.querySelector('h2')?.innerText || '').trim(),
                    place: (a.querySelector('p')?.innerText || '').trim(),
                    page: a.href,
                    logo: a.querySelector('.gallery_img img')?.src || '',
                    cover: (a.querySelector('.pic')?.style.backgroundImage || '').replace(/^url\(["']?/, '').replace(/["']?\)$/, '')
                })).filter(x => x.name && x.logo)
            """))
        browser.close()
    seen = {}
    for row in rows:
        seen.setdefault(norm(row["name"]), row)
    return list(seen.values())

def download(ctx, name, url):
    r = ctx.request.get(url, timeout=15000)
    if not r.ok:
        return ""
    body = r.body()
    ctype = (r.headers.get("content-type") or "").lower()
    if len(body) <= 500 or not (ctype.startswith("image/") or re.search(r"\.(svg|png|jpe?g|webp|ico)(?:[?#]|$)", url, re.I)):
        return ""
    fn = slug(name) + ext_of(url, ctype)
    path = os.path.join(LOGODIR, fn)
    open(path, "wb").write(body)
    return "logos/artemperor/" + fn

def main():
    candidates = venue_names_without_local_official_logo()
    scraped = scrape()
    matched = []
    for row in scraped:
        venue = match_venue(row["name"], candidates)
        if venue:
            matched.append({**row, "venue": venue})

    existing = {}
    if os.path.exists(OUT):
        try:
            existing = json.load(open(OUT, encoding="utf-8")).get("logos", {})
        except Exception:
            existing = {}

    from playwright.sync_api import sync_playwright
    with sync_playwright() as p:
        browser = p.chromium.launch()
        ctx = browser.new_context(ignore_https_errors=True)
        logos = dict(existing)
        downloaded = 0
        for row in matched:
            if logos.get(row["venue"]) and os.path.exists(P(logos[row["venue"]])):
                continue
            got = download(ctx, row["venue"], row["logo"])
            if got:
                logos[row["venue"]] = got
                downloaded += 1
        browser.close()

    out = {
        "_source": "https://artemperor.tw/museums?page=1..8",
        "_note": "Fallback logos only. Official local logos from logo_map.json stay higher priority.",
        "logos": dict(sorted(logos.items())),
        "matched": sorted(
            [{"venue": r["venue"], "artemperor_name": r["name"], "page": r["page"], "logo": r["logo"]} for r in matched],
            key=lambda x: x["venue"],
        ),
    }
    json.dump(out, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(json.dumps({"scraped": len(scraped), "matched": len(matched), "downloaded": downloaded, "logos": len(out["logos"])}, ensure_ascii=False))

if __name__ == "__main__":
    main()
