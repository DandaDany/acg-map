#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Collect Soka Art exhibitions from the official detail pages.

Soka has both Taipei and Tainan spaces. The exhibition list page does not carry
enough location detail, so this collector opens each detail page and assigns the
event to the matching branch.

Output:
  soka_extra.json  official events grouped by Soka branch
"""
import datetime
from paths import path as P
import html
import json
import os
import re
import ssl
import urllib.request
from html.parser import HTMLParser
from urllib.parse import urljoin

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = P("soka_extra.json")
BASE = "https://www.soka-art.com"
LIST_URLS = [
    "https://www.soka-art.com/cn/exhibition/current",
    "https://www.soka-art.com/cn/exhibition/future",
    "https://www.soka-art.com/cn/exhibition",
]
UA = "tw-exhibition-map-soka/0.1 local maintenance"
TODAY = datetime.date.today()

BRANCHES = {
    "tainan": {
        "name": "索卡藝術 台南空間",
        "city": "台南市",
        "addr": "臺南市安平區慶平路446號",
        "lat": 22.99728953725815,
        "lng": 120.1748699153447,
    },
    "taipei": {
        "name": "索卡藝術 台北空間",
        "city": "台北市",
        "addr": "台北市中山區堤頂大道二段350號",
        "lat": 25.07965141055217,
        "lng": 121.56333144232764,
    },
}

_SSL_CTX = ssl.create_default_context()
_SSL_CTX.verify_flags &= ~ssl.VERIFY_X509_STRICT


class VisibleText(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.parts = []
        self._skip = 0

    def handle_starttag(self, tag, attrs):
        if tag in ("script", "style", "noscript"):
            self._skip += 1

    def handle_endtag(self, tag):
        if tag in ("script", "style", "noscript") and self._skip:
            self._skip -= 1

    def handle_data(self, data):
        if not self._skip:
            text = re.sub(r"\s+", " ", html.unescape(data or "")).strip()
            if text:
                self.parts.append(text)


def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=30, context=_SSL_CTX) as r:
        data = r.read().decode("utf-8", "replace")
        return data, r.geturl()


def strip_text(markup):
    parser = VisibleText()
    parser.feed(markup)
    return re.sub(r"\s+", " ", " ".join(parser.parts)).strip()


def clean_title(text):
    text = html.unescape(text or "")
    text = re.sub(r"\s+", " ", text).strip()
    text = re.sub(r"\s*[-｜|]\s*(展览|展覽)\s*[-｜|]\s*索卡.*$", "", text, flags=re.I)
    text = re.sub(r"\s*[-｜|]\s*索卡.*$", "", text, flags=re.I)
    return text.strip()


def page_title(markup):
    m = re.search(r"<title[^>]*>(.*?)</title>", markup, flags=re.I | re.S)
    if m:
        title = clean_title(re.sub(r"<[^>]+>", " ", m.group(1)))
        if title:
            return title
    m = re.search(r"<h[12][^>]*>(.*?)</h[12]>", markup, flags=re.I | re.S)
    if m:
        title = clean_title(re.sub(r"<[^>]+>", " ", m.group(1)))
        if title:
            return title
    return ""


def parse_date_range(text):
    m = re.search(r"(20\d{2})[./-](\d{1,2})[./-](\d{1,2})\s*[-–—]\s*(?:(20\d{2})[./-])?(\d{1,2})[./-](\d{1,2})", text)
    if not m:
        return "", ""
    y1, mo1, d1, y2, mo2, d2 = m.groups()
    y2 = y2 or y1
    start = f"{int(y1):04d}/{int(mo1):02d}/{int(d1):02d}"
    end = f"{int(y2):04d}/{int(mo2):02d}/{int(d2):02d}"
    return start, end


def end_date(value):
    try:
        return datetime.datetime.strptime(value, "%Y/%m/%d").date()
    except Exception:
        return None


def find_image(markup, base_url):
    imgs = []
    for m in re.finditer(r"<img\b[^>]+>", markup, flags=re.I):
        tag = m.group(0)
        attrs = dict((k.lower(), html.unescape(v)) for k, v in re.findall(r'([\w:-]+)\s*=\s*["\']([^"\']+)["\']', tag))
        src = attrs.get("data-src") or attrs.get("src") or ""
        if not src:
            continue
        if re.search(r"logo|icon|address|map|loading|blank|qrcode|qr", src, flags=re.I):
            continue
        if "/Uploads/" not in src and "/uploads/" not in src:
            continue
        imgs.append(urljoin(base_url, src))
    return imgs[0] if imgs else ""


def detail_links(markup, base_url):
    links = []
    for href in re.findall(r'href\s*=\s*["\']([^"\']*?/exhibition/details/\d+[^"\']*)["\']', markup, flags=re.I):
        links.append(urljoin(base_url, href))
    return links


def branch_for(text):
    # Detail pages render as: title + date range + location. The footer contains
    # every branch address, so only inspect the short text after the date range.
    m = re.search(r"20\d{2}[./-]\d{1,2}[./-]\d{1,2}\s*[-–—]\s*(?:20\d{2}[./-])?\d{1,2}[./-]\d{1,2}", text)
    window = text[m.end():m.end() + 180] if m else text[:260]
    if "慶平路446號" in window or "庆平路446号" in window:
        return "tainan"
    if re.search(r"(台南|臺南|索卡.{0,4}台南|索卡.{0,4}臺南)", window):
        return "tainan"
    if re.search(r"(台北|臺北|索卡.{0,4}台北|索卡.{0,4}臺北)", window):
        return "taipei"
    return "taipei"


def collect():
    found = []
    seen = set()
    for url in LIST_URLS:
        try:
            markup, base = fetch(url)
        except Exception as exc:
            print(f"LIST_FAIL {url}: {exc}")
            continue
        for link in detail_links(markup, base):
            if link not in seen:
                seen.add(link)
                found.append(link)

    grouped = {info["name"]: {**info, "loc": "exact", "url": BASE + "/cn/exhibition", "ex": []} for info in BRANCHES.values()}
    for link in found:
        try:
            markup, base = fetch(link)
        except Exception as exc:
            print(f"DETAIL_FAIL {link}: {exc}")
            continue
        text = strip_text(markup)
        title = page_title(markup)
        start, end = parse_date_range(text)
        if not title or not (start or end):
            continue
        ed = end_date(end)
        if ed and ed < TODAY:
            continue
        branch = branch_for(text)
        info = BRANCHES[branch]
        grouped[info["name"]]["ex"].append({
            "t": title,
            "s": start,
            "e": end,
            "l": base,
            "img": find_image(markup, base),
        })

    return {name: info for name, info in grouped.items() if info.get("ex")}


def main():
    data = collect()
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"WROTE {OUT} venues={len(data)} events={sum(len(v['ex']) for v in data.values())}")


if __name__ == "__main__":
    main()
