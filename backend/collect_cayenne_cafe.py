#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Collect Cayenne Cafe ACG theme cafe events from official pages.

Outputs:
  cayenne_stores.json  normalized restaurant/news records
  cayenne_extra.json   ACG-related Cayenne events for refresh_venues.py
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

_SSL_CTX = ssl.create_default_context()
_SSL_CTX.verify_flags &= ~ssl.VERIFY_X509_STRICT

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = P("cayenne_stores.json")
EXTRA = P("cayenne_extra.json")
UA = "tw-exhibition-map-cayenne/0.1 local maintenance"

NEWS_URL = "https://www.cayenne-cafe.com.tw/news.aspx"
RESTAURANT_URL = "https://www.cayenne-cafe.com.tw/restaurant.aspx"
CITY = r"(台北市|臺北市|新北市|桃園市|台中市|臺中市|台南市|臺南市|高雄市|基隆市|新竹市|新竹縣|苗栗縣|彰化縣|南投縣|雲林縣|嘉義市|嘉義縣|屏東縣|宜蘭縣|花蓮縣|台東縣|臺東縣|澎湖縣|金門縣|連江縣)"
CITY_RE = re.compile(CITY)
DATE_RE = re.compile(r"(\d{4})[/-](\d{1,2})[/-](\d{1,2})")
STORE_RE = re.compile(r"(?:(?:台北|臺北|台中|臺中|台南|臺南|高雄)\s*)?([一-龥A-Za-z0-9]+店)")
SKIP_NEWS = re.compile(r"公告|營業時間|公休|店休|暫停|停業|開幕|徵才|菜單|餐點|點餐|訂位|外帶")


class LinkTextParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.links = []
        self._stack = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "a" and attrs.get("href"):
            self._stack.append({"href": attrs["href"], "text": []})

    def handle_endtag(self, tag):
        if tag == "a" and self._stack:
            item = self._stack.pop()
            text = clean_text(" ".join(item["text"]))
            if text:
                self.links.append({"href": item["href"], "text": text})

    def handle_data(self, data):
        if self._stack:
            self._stack[-1]["text"].append(data)


class TextParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.items = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "img" and attrs.get("alt"):
            self._push(attrs["alt"])

    def handle_data(self, data):
        self._push(data)

    def _push(self, text):
        text = clean_text(text)
        if text:
            self.items.append(text)


def norm(text):
    return (text or "").replace("臺", "台").strip()


def clean_text(text):
    text = html.unescape(text or "")
    text = re.sub(r"\s+", " ", text).strip()
    return text


def clean_addr(text):
    return re.sub(r"^\s*\d{3,6}\s*", "", norm(text))


def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=30, context=_SSL_CTX) as r:
        raw = r.read()
    for enc in ("utf-8", "big5", "cp950"):
        try:
            return raw.decode(enc)
        except UnicodeDecodeError:
            pass
    return raw.decode("utf-8", "replace")


def fmt_date(match):
    return f"{int(match.group(1)):04d}/{int(match.group(2)):02d}/{int(match.group(3)):02d}"


def parse_restaurants(markup):
    parser = TextParser()
    parser.feed(markup)
    stores = []
    current = None
    for item in parser.items:
        item = norm(item)
        if "凱岩" in item and "店" in item and not CITY_RE.search(item):
            m = STORE_RE.search(item)
            if not m:
                continue
            current = {"title": item, "store": m.group(1), "addr": "", "source": RESTAURANT_URL}
            stores.append(current)
            continue
        if current and not current["addr"] and CITY_RE.search(item) and re.search(r"[區鄉鎮市].*[路街道段巷弄號]|[路街道段巷弄號]", item):
            current["addr"] = clean_addr(item)
    return [s for s in stores if s.get("addr")]


def parse_news(markup):
    parser = LinkTextParser()
    parser.feed(markup)
    out = []
    seen = set()
    for link in parser.links:
        text = norm(link["text"])
        dates = list(DATE_RE.finditer(text))
        mstore = STORE_RE.search(text)
        if not mstore or len(dates) < 2:
            continue
        store = mstore.group(1)
        start, end = fmt_date(dates[0]), fmt_date(dates[1])
        title = text[:dates[0].start()].strip(" -–—")
        title = re.sub(r"^(台北|台中|台南|高雄)\s*", "", title)
        title = re.sub(r"^" + re.escape(store), "", title).strip(" -–—")
        if not title or SKIP_NEWS.search(title):
            continue
        href = urljoin(NEWS_URL, link["href"])
        key = (store, title, start, end)
        if key in seen:
            continue
        seen.add(key)
        out.append({"store": store, "title": title, "start": start, "end": end, "source": href})
    return out


def build_extra(stores, news):
    by_store = {s["store"]: s for s in stores}
    out = {}
    for item in news:
        store = by_store.get(item["store"])
        if not store:
            continue
        name = store["title"]
        rec = out.setdefault(name, {
            "addr": store["addr"],
            "url": item["source"],
            "ex": [],
        })
        rec["ex"].append({
            "t": item["title"],
            "s": item["start"],
            "e": item["end"],
            "l": item["source"],
            "img": "",
        })
    return out


def main():
    restaurant_html = fetch(RESTAURANT_URL)
    news_html = fetch(NEWS_URL)
    stores = parse_restaurants(restaurant_html)
    news = parse_news(news_html)
    json.dump({
        "_note": "Generated from official Cayenne Cafe restaurant/news pages.",
        "restaurant_url": RESTAURANT_URL,
        "news_url": NEWS_URL,
        "stores": stores,
        "news": news,
    }, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    extra = build_extra(stores, news)
    json.dump({
        "_note": "ACG-related Cayenne Cafe events generated from cayenne_stores.json.",
        "venues": extra,
    }, open(EXTRA, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    current = sum(1 for info in extra.values() for e in info["ex"] if not e.get("e") or e["e"] >= datetime.date.today().strftime("%Y/%m/%d"))
    print(json.dumps({"stores": len(stores), "news": len(news), "venues": len(extra), "current_events": current}, ensure_ascii=False))


if __name__ == "__main__":
    main()
