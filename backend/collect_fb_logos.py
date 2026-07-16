#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Download local fallback logos from official Facebook page avatars.

Input:  fb_pages.json  {"pages": {"場館名": "https://www.facebook.com/page/"}}
        + current venues.json Facebook links are auto-merged into fb_pages.json.
Output: fb_logos.json  {"logos": {"場館名": "logos/facebook/場館名.jpg"}}

Facebook is a fallback layer only. Official site logos and artemperor fallback
stay higher priority in refresh_venues.py.
"""
import hashlib, json, os, re
from paths import path as P
from io import BytesIO
from urllib.parse import urlparse

from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
PAGES = P("fb_pages.json")
OUT = P("fb_logos.json")
LOGODIR = P("logos", "facebook")
PROFILE_DIR = os.environ.get("FB_LOGO_PROFILE_DIR", P("profiles", "fb_logo_chrome"))
BAD_IMAGE_MD5 = {
    "3e8f62364b0f574a7d18a6c8b26730f1",
    "1dd14f9a1e1f8f374bb29ccb8c8a2b82",
}
BAD_IMAGE_SIZES = {1876}
os.makedirs(LOGODIR, exist_ok=True)

def slug(name):
    s = re.sub(r"\s+", "", (name or "").strip()).lower()
    s = re.sub(r"[^a-z0-9\u4e00-\u9fff]+", "_", s)
    return s.strip("_")[:80] or "venue"

def page_key(url):
    parsed = urlparse(url)
    path = parsed.path.strip("/")
    if path == "profile.php":
        qs = dict(part.split("=", 1) for part in parsed.query.split("&") if "=" in part)
        return qs.get("id", "")
    if not path:
        return ""
    parts = path.split("/")
    if parts[0] == "p" and len(parts) >= 2:
        m = re.search(r"-(\d{8,})$", parts[1])
        return m.group(1) if m else ""
    return parts[0]

def canonical_page_url(url):
    parsed = urlparse(url)
    if "facebook.com" not in (parsed.hostname or ""):
        return ""
    path = parsed.path.strip("/")
    if not path:
        return ""
    if path == "profile.php":
        key = page_key(url)
        return f"https://www.facebook.com/profile.php?id={key}" if key else ""
    parts = path.split("/")
    if parts[0] == "p":
        return "https://www.facebook.com/" + "/".join(parts[:2])
    return "https://www.facebook.com/" + parts[0] + "/"

def sync_pages_from_venues(pages):
    vpath = P("venues.json")
    if not os.path.exists(vpath):
        return 0
    try:
        venues = json.load(open(vpath, encoding="utf-8")).get("venues", [])
    except Exception:
        return 0
    added = 0
    for v in venues:
        if v.get("logo") or v.get("name") in pages:
            continue
        links = []
        if v.get("url"):
            links.append(v["url"])
        for e in v.get("ex", []):
            if e.get("l"):
                links.append(e["l"])
        for link in links:
            page = canonical_page_url(link)
            if page and page_key(page):
                pages[v["name"]] = page
                added += 1
                break
    if added:
        json.dump({"pages": dict(sorted(pages.items()))}, open(PAGES, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    return added

def ext_of(url, ctype=""):
    path = urlparse(url).path
    m = re.search(r"\.(png|jpe?g|webp)(?:$|[?#])", path, re.I)
    if m:
        return "." + m.group(1).lower().replace("jpeg", "jpg")
    if "png" in ctype:
        return ".png"
    if "webp" in ctype:
        return ".webp"
    return ".jpg"

def download_image(ctx, url, venue):
    r = ctx.request.get(url, timeout=20000)
    if not r.ok:
        return ""
    body = r.body()
    ctype = (r.headers.get("content-type") or "").lower()
    if len(body) < 500 or not ctype.startswith("image/"):
        return ""
    digest = hashlib.md5(body).hexdigest()
    if digest in BAD_IMAGE_MD5 or len(body) in BAD_IMAGE_SIZES:
        return ""
    try:
        img = Image.open(BytesIO(body))
        width, height = img.size
    except Exception:
        return ""
    ratio = width / height if height else 0
    if width < 120 or height < 120 or ratio < 0.8 or ratio > 1.25:
        return ""
    fn = slug(venue) + ext_of(r.url, ctype)
    path = os.path.join(LOGODIR, fn)
    open(path, "wb").write(body)
    return "logos/facebook/" + fn

def page_avatar_fallback(page, ctx, venue, url):
    try:
        page.goto(url, wait_until="domcontentloaded", timeout=20000)
        page.wait_for_timeout(1800)
        candidates = page.evaluate("""
        () => {
          const out = [];
          document.querySelectorAll('meta[property="og:image"],meta[name="twitter:image"]').forEach(m => {
            if (m.content) out.push(m.content);
          });
          document.querySelectorAll('image,img').forEach(el => {
            const src = el.currentSrc || el.src || el.href?.baseVal || el.href?.animVal ||
              el.getAttribute('xlink:href') || el.getAttribute('href') ||
              el.getAttributeNS?.('http://www.w3.org/1999/xlink', 'href') || '';
            const r = el.getBoundingClientRect();
            if (src && r.top < 420 && r.width >= 40 && r.height >= 40) out.push(src);
          });
          return [...new Set(out)].slice(0, 12);
        }
        """)
    except Exception:
        return ""
    for cand in candidates:
        if not cand or "emoji.php" in cand or "static.xx.fbcdn.net" in cand:
            continue
        try:
            got = download_image(ctx, cand, venue)
            if got:
                return got
        except Exception:
            continue
    return ""

def main():
    pages = json.load(open(PAGES, encoding="utf-8")).get("pages", {}) if os.path.exists(PAGES) else {}
    auto_added = sync_pages_from_venues(pages)
    existing = {}
    if os.path.exists(OUT):
        try:
            existing = json.load(open(OUT, encoding="utf-8")).get("logos", {})
        except Exception:
            existing = {}

    from playwright.sync_api import sync_playwright
    with sync_playwright() as p:
        browser = None
        if os.path.isdir(PROFILE_DIR):
            ctx = p.chromium.launch_persistent_context(
                PROFILE_DIR,
                headless=True,
                ignore_https_errors=True,
                user_agent="Mozilla/5.0",
            )
        else:
            browser = p.chromium.launch()
            ctx = browser.new_context(ignore_https_errors=True, user_agent="Mozilla/5.0")
        pg = ctx.new_page()
        logos = dict(existing)
        downloaded = 0
        for venue, page_url in pages.items():
            if logos.get(venue) and os.path.exists(P(logos[venue])):
                continue
            key = page_key(page_url)
            if not key:
                continue
            graph = f"https://graph.facebook.com/{key}/picture?type=large"
            got = download_image(ctx, graph, venue)
            if not got:
                got = page_avatar_fallback(pg, ctx, venue, page_url)
            if got:
                logos[venue] = got
                downloaded += 1
        ctx.close()
        if browser:
            browser.close()

    json.dump({
        "_note": "Facebook avatar fallback logos. Generated by collect_fb_logos.py from fb_pages.json.",
        "logos": dict(sorted(logos.items())),
    }, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(json.dumps({"pages": len(pages), "auto_added": auto_added, "downloaded": downloaded, "logos": len(logos)}, ensure_ascii=False))

if __name__ == "__main__":
    main()
