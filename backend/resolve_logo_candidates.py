#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Resolve logo source candidates from the missing-logo report.

This is a conservative helper for the "can_try_with_network_later" bucket:
it follows short/event/social URLs, looks for official-site and Facebook links,
and writes a reviewable report. It does not modify logo mappings.
"""
import json
from paths import path as P
import os
import re
import ssl
import sys
import urllib.request
from urllib.parse import urlparse

HERE = os.path.dirname(os.path.abspath(__file__))
INP = P("_missing_logo_report.json")
OUT = P("_resolved_logo_candidates.json")
UA = "tw-exhibition-map-logo-resolver/0.1 local maintenance"

_SSL_CTX = ssl.create_default_context()
_SSL_CTX.verify_flags &= ~ssl.VERIFY_X509_STRICT

BAD_DOMAINS = {
    "cloud.culture.tw", "s3.resource.opentix.life", "opentix.life",
    "www.opentix.life", "ticket.com.tw", "www.ticket.com.tw",
    "imgs2.utiki.com.tw", "tw.news.yahoo.com", "news.yahoo.com",
    "instagram.com", "www.instagram.com",
}
EVENT_DOMAINS = re.compile(r"(opentix|cloud\.culture|ticket\.com|yahoo\.com|instagram\.com|facebook\.com/share|facebook\.com/events)", re.I)


def domain(url):
    try:
        host = urlparse(url).netloc.lower()
        return host[4:] if host.startswith("www.") else host
    except Exception:
        return ""


def clean_fb(url):
    if not url or "facebook.com" not in url:
        return ""
    url = url.split("?")[0].split("#")[0].rstrip("/")
    if re.search(r"/(share|sharer|plugins|dialog|login|events|posts|photos)(/|$)", url):
        return ""
    return url


def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=20, context=_SSL_CTX) as resp:
        final = resp.geturl()
        ctype = (resp.headers.get("content-type") or "").lower()
        data = b""
        if "text/html" in ctype or "application/xhtml" in ctype or not ctype:
            data = resp.read(350000)
        return final, ctype, data.decode("utf-8", "replace")


def links_from_html(final_url, html):
    out = []
    for m in re.finditer(r'href=["\']([^"\']+)["\']', html or "", re.I):
        href = m.group(1)
        try:
            href = urllib.request.urljoin(final_url, href)
        except Exception:
            pass
        out.append(href)
    return out


def score_candidate(venue, url):
    d = domain(url)
    if not d or d in BAD_DOMAINS:
        return 0
    score = 1
    if "facebook.com" in d:
        score += 2
    if EVENT_DOMAINS.search(url):
        score -= 2
    compact_name = re.sub(r"[^0-9A-Za-z一-龥]+", "", venue.lower())
    compact_host = re.sub(r"[^0-9a-z]+", "", d.lower())
    for token in re.findall(r"[A-Za-z]{4,}|[一-龥]{2,}", venue):
        token = token.lower()
        if token and token in d.lower():
            score += 3
    if compact_host and compact_host in compact_name:
        score += 2
    return score


def main():
    data = json.load(open(INP, encoding="utf-8"))
    rows = data.get("can_try_with_network_later", [])
    results = {}
    for row in rows:
        name = row["name"]
        found = []
        errors = []
        for url in row.get("urls", []):
            try:
                final, ctype, html = fetch(url)
                found.append({"kind": "resolved", "url": final, "domain": domain(final), "score": score_candidate(name, final)})
                for href in links_from_html(final, html):
                    d = domain(href)
                    if not d:
                        continue
                    if "facebook.com" in d:
                        fb = clean_fb(href)
                        if fb:
                            found.append({"kind": "facebook", "url": fb, "domain": domain(fb), "score": score_candidate(name, fb)})
                    elif d not in BAD_DOMAINS and score_candidate(name, href) >= 2:
                        found.append({"kind": "site", "url": href, "domain": d, "score": score_candidate(name, href)})
            except Exception as e:
                errors.append({"url": url, "error": type(e).__name__, "message": str(e)[:160]})
        seen = set()
        deduped = []
        for item in sorted(found, key=lambda x: x.get("score", 0), reverse=True):
            key = item.get("url")
            if key in seen:
                continue
            seen.add(key)
            deduped.append(item)
        results[name] = {"city": row.get("city", ""), "addr": row.get("addr", ""), "candidates": deduped[:12], "errors": errors}
        print(name, len(deduped), file=sys.stderr)
    json.dump(results, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(json.dumps({"venues": len(results), "out": OUT}, ensure_ascii=False))


if __name__ == "__main__":
    main()
