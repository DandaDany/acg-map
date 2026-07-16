#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Fetch missing event KV images from event links and cache them.

The script reads venues.json, visits events with a link but no img, extracts a
likely main visual, validates it as a real image, and writes event_kv_cache.json.
refresh_venues.py then applies that cache on every run.
"""
import datetime
from paths import path as P
import argparse
import json
import os
import re
import ssl
import sys
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from html import unescape
from urllib.parse import quote, unquote, urljoin, urlparse, urlunparse

HERE = os.path.dirname(os.path.abspath(__file__))
VENUES = P("venues.json")
CACHE = P("event_kv_cache.json")
TODAY = datetime.date.today().strftime("%Y/%m/%d")

_SSL_CTX = ssl._create_unverified_context()

UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Safari/537.36"
BAD_IMG = re.compile(
    r"(logo|favicon|icon|sprite|avatar|profile|btn[-_]|_btn|header|footer|transparent|blank|"
    r"no[-_]?pic|aplus\.png|egov\.png|/bg\.png|loading\.gif|tribe-loading|scrollup|"
    r"social-share|qrcode|qr-code|/images/top\.png(?:$|\?)|\.svg(?:$|\?)|"
    r"/images/img\.jpg(?:$|\?)|/images/aa\.jpg(?:$|\?)|/images/s5_1\.png(?:$|\?))",
    re.I,
)
GOOD_IMG = re.compile(r"(poster|kv|keyvisual|visual|banner|cover|exhibition|activity|news|upload|uploads|relpic|userfiles|photo|image|jpg|jpeg|png|webp)", re.I)
BAD_HOST = re.compile(r"(googletagmanager|doubleclick|gravatar|reurl\.cc/asset)", re.I)
SOCIAL_DETAIL = re.compile(r"(facebook\.com/.+/(posts|photos|events|permalink)|instagram\.com/p/)", re.I)
SOCIAL_HOST = re.compile(r"(^|\.)facebook\.com$|(^|\.)instagram\.com$", re.I)
HTTPS_ONLY_HOSTS = {"taoyuantudigong.org.tw"}


def log(*args):
    print(*args, file=sys.stderr)


def load_json(path, default):
    try:
        return json.load(open(path, encoding="utf-8"))
    except Exception:
        return default


def is_home(url):
    try:
        path = urlparse(url).path.strip("/")
        return path == "" or path.lower() in ("index.html", "index.php", "home", "default.aspx", "ch", "zh-tw")
    except Exception:
        return False


def quote_url(url):
    try:
        p = urlparse(url)
        scheme = "https" if p.scheme == "http" and p.netloc.lower().replace("www.", "") in HTTPS_ONLY_HOSTS else p.scheme
        path = quote(unquote(p.path), safe="/%:@")
        query = quote(unquote(p.query), safe="=&?/%:@,+")
        return urlunparse((scheme, p.netloc, path, p.params, query, p.fragment))
    except Exception:
        return url


def request(url, timeout=15):
    url = quote_url(url)
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept-Language": "zh-TW,zh;q=0.9,en;q=0.6"})
    return urllib.request.urlopen(req, timeout=timeout, context=_SSL_CTX)


def clean_url(url, base):
    url = unescape((url or "").strip())
    if not url or url.startswith(("data:", "javascript:", "mailto:")):
        return ""
    if url.startswith("//"):
        url = "https:" + url
    return urljoin(base, url)


def fetch_html(url):
    with request(url) as r:
        data = r.read(800000)
        base = r.geturl()
    return data.decode("utf-8", "ignore"), base


def image_ok(url):
    if not url or BAD_HOST.search(url) or BAD_IMG.search(url):
        return False
    try:
        with request(url, timeout=12) as r:
            ct = (r.headers.get("Content-Type", "") or "").lower()
            data = r.read(70000)
        return ct.startswith("image/") and len(data) > 3000
    except Exception:
        return False


def attrs(tag):
    return {
        m.group(1).lower(): unescape(m.group(2).strip())
        for m in re.finditer(r'([:\w-]+)\s*=\s*["\']([^"\']*)["\']', tag, re.I)
    }


def meta_candidates(html, base):
    out = []
    for m in re.finditer(r"<meta[^>]+>", html, re.I):
        at = attrs(m.group(0))
        key = (at.get("property") or at.get("name") or "").lower()
        if key in ("og:image", "og:image:secure_url", "twitter:image", "twitter:image:src"):
            u = clean_url(at.get("content", ""), base)
            if u:
                out.append((1200, u))
    for m in re.finditer(r"<link[^>]+>", html, re.I):
        at = attrs(m.group(0))
        if "image_src" in (at.get("rel") or "").lower():
            u = clean_url(at.get("href", ""), base)
            if u:
                out.append((1200, u))
    patterns = [
        r'<meta[^>]+property=["\']og:image:secure_url["\'][^>]+content=["\']([^"\']+)',
        r'<meta[^>]+property=["\']og:image["\'][^>]+content=["\']([^"\']+)',
        r'<meta[^>]+content=["\']([^"\']+)["\'][^>]+property=["\']og:image',
        r'<meta[^>]+name=["\']twitter:image(?::src)?["\'][^>]+content=["\']([^"\']+)',
        r'<link[^>]+rel=["\']image_src["\'][^>]+href=["\']([^"\']+)',
        r'"image"\s*:\s*"([^"]+\.(?:jpg|jpeg|png|webp)[^"]*)"',
    ]
    for p in patterns:
        for m in re.finditer(p, html, re.I):
            u = clean_url(m.group(1), base)
            if u:
                out.append((1200, u))
    return out


def img_candidates(html, base):
    out = []
    for m in re.finditer(r"<img[^>]+>", html, re.I):
        tag = m.group(0)
        at = attrs(tag)
        values = []
        for name in ("src", "data-src", "data-original", "data-lazy", "data-url"):
            if at.get(name):
                values.append(at[name])
        if at.get("srcset"):
            for part in at["srcset"].split(","):
                values.append(part.strip().split(" ")[0])
        if not values:
            continue
        score = 100
        for attr, weight in (("width", 1), ("height", 1)):
            if at.get(attr, "").isdigit():
                score += min(int(at[attr]), 1400) * weight
        for raw in values:
            u = clean_url(raw, base)
            if not u:
                continue
            u_score = score
            if GOOD_IMG.search(u) or GOOD_IMG.search(tag):
                u_score += 700
            if BAD_IMG.search(u) or BAD_IMG.search(tag):
                u_score -= 1500
            out.append((u_score, u))
    for m in re.finditer(r'https?://[^"\'>\s]+\.(?:jpg|jpeg|png|webp)(?:\?[^"\'>\s]*)?', html, re.I):
        u = clean_url(m.group(0), base)
        if u:
            out.append((650 if GOOD_IMG.search(u) else 250, u))
    return out


def extract_kv(url):
    html, base = fetch_html(url)
    tm = re.search(r'<input[^>]+id=["\']target["\'][^>]+value=["\']([^"\']+)', html, re.I)
    if tm:
        target = clean_url(tm.group(1), base)
        if target and urlparse(target).netloc != urlparse(base).netloc:
            html, base = fetch_html(target)
    bm = re.search(r'<base[^>]+href=["\']([^"\']+)', html, re.I)
    if bm:
        base = clean_url(bm.group(1), base) or base
    seen = set()
    candidates = meta_candidates(html, base) + img_candidates(html, base)
    for _score, img in sorted(candidates, reverse=True):
        if img in seen:
            continue
        seen.add(img)
        if image_ok(img):
            return img
    return ""


def extract_kv_browser(url):
    from playwright.sync_api import sync_playwright

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(
            ignore_https_errors=True,
            locale="zh-TW",
            user_agent=UA,
        )
        try:
            page.goto(url, wait_until="domcontentloaded", timeout=45000)
            page.wait_for_timeout(2500)
            candidates = page.evaluate(
                """() => {
                    const out = [];
                    document.querySelectorAll('meta[property="og:image"],meta[property="og:image:secure_url"],meta[name="twitter:image"],meta[name="twitter:image:src"]').forEach(m => {
                        if (m.content) out.push({score: 1200, src: m.content, w: 0, h: 0, meta: true});
                    });
                    [...document.images].forEach(img => {
                        const src = img.currentSrc || img.src;
                        if (!src || src.startsWith('data:')) return;
                        const area = (img.naturalWidth || 0) * (img.naturalHeight || 0);
                        out.push({score: 100 + Math.min(area / 1000, 1800), src, w: img.naturalWidth || 0, h: img.naturalHeight || 0, meta: false});
                    });
                    return out.sort((a, b) => b.score - a.score).slice(0, 40);
                }"""
            )
        finally:
            browser.close()
    seen = set()
    for item in candidates:
        img = item.get("src", "")
        if not img or img in seen:
            continue
        seen.add(img)
        if BAD_HOST.search(img) or BAD_IMG.search(img):
            continue
        if item.get("w", 0) * item.get("h", 0) >= 90000:
            return img
        if item.get("meta") and image_ok(img):
            return img
    return ""


def event_links(skip_social=False):
    data = load_json(VENUES, {}).get("venues", [])
    links = {}
    for v in data:
        for e in v.get("ex", []):
            link = (e.get("l") or "").strip()
            if e.get("img") or not link.startswith(("http://", "https://")):
                continue
            host = urlparse(link).netloc.lower().replace("www.", "")
            if skip_social and SOCIAL_HOST.search(host):
                continue
            # Home pages usually expose logos/cover art, not event KV. Social post/photo pages are still useful.
            if e.get("h") and not SOCIAL_DETAIL.search(link):
                continue
            links.setdefault(link, {"venue": v.get("name", ""), "title": e.get("t", "")})
    return links


def main():
    parser = argparse.ArgumentParser(description="Fetch missing event KV images from event links.")
    parser.add_argument(
        "--skip-social",
        action="store_true",
        help="skip Facebook/Instagram links and fetch only non-social event pages",
    )
    parser.add_argument(
        "--browser-fallback",
        action="store_true",
        help="for pages still missing KV, use Playwright to inspect rendered images",
    )
    args = parser.parse_args()

    cache = load_json(CACHE, {"updated": "", "links": {}})
    cache.setdefault("links", {})
    links = event_links(skip_social=args.skip_social)
    todo = [u for u in links if u not in cache["links"]]
    log("KV 缺圖連結:", len(links), "｜已快取:", len(cache["links"]), "｜待抓:", len(todo))

    def one(url):
        try:
            img = extract_kv(url)
            return url, {"ok": bool(img), "img": img, "code": "ok" if img else "no_image", "updated": TODAY}
        except Exception as e:
            return url, {"ok": False, "img": "", "code": type(e).__name__, "updated": TODAY}

    if todo:
        with ThreadPoolExecutor(max_workers=10) as ex:
            futs = [ex.submit(one, u) for u in todo]
            for fut in as_completed(futs):
                url, rec = fut.result()
                cache["links"][url] = rec
                if rec.get("img"):
                    log("KV", links[url]["venue"], "｜", links[url]["title"], "=>", rec["img"])
        cache["updated"] = TODAY
        json.dump(cache, open(CACHE, "w", encoding="utf-8"), ensure_ascii=False, indent=2)

    if args.browser_fallback:
        browser_todo = [u for u in links if not cache["links"].get(u, {}).get("img")]
        if browser_todo:
            log("瀏覽器 fallback 待抓:", len(browser_todo))
        for url in browser_todo:
            try:
                img = extract_kv_browser(url)
                rec = {"ok": bool(img), "img": img, "code": "ok_browser" if img else "no_image_browser", "updated": TODAY}
            except Exception as e:
                rec = {"ok": False, "img": "", "code": type(e).__name__, "updated": TODAY}
            cache["links"][url] = rec
            if rec.get("img"):
                log("KV(browser)", links[url]["venue"], "｜", links[url]["title"], "=>", rec["img"])
        cache["updated"] = TODAY
        json.dump(cache, open(CACHE, "w", encoding="utf-8"), ensure_ascii=False, indent=2)

    hits = sum(1 for u in links if cache["links"].get(u, {}).get("img"))
    print(json.dumps({"links": len(links), "cached": len(cache["links"]), "with_kv": hits, "todo": len(todo)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
