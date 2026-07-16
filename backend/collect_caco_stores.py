#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Collect CACO CAFE / POPUP store data from official storelist pages.

Outputs:
  caco_stores.json  raw normalized CAFE and POPUP store records
  caco_extra.json   ACG-related CACO POPUP events for refresh_venues.py
"""
import datetime
from paths import path as P
import html
import json
import os
import re
import urllib.request
from html.parser import HTMLParser

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = P("caco_stores.json")
EXTRA = P("caco_extra.json")
UA = "tw-exhibition-map-caco/0.1 local maintenance"

CAFE_URL = "https://www.caco.com.tw/storelist/CAFE"
POPUP_URL = "https://www.caco.com.tw/storelist/POPUP"
CITY = r"(台北市|臺北市|新北市|桃園市|台中市|臺中市|台南市|臺南市|高雄市|基隆市|新竹市|新竹縣|苗栗縣|彰化縣|南投縣|雲林縣|嘉義市|嘉義縣|屏東縣|宜蘭縣|花蓮縣|台東縣|臺東縣|澎湖縣|金門縣|連江縣)"
CITY_RE = re.compile(CITY)


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
        text = html.unescape(text or "")
        text = re.sub(r"\s+", " ", text).strip()
        if not text:
            return
        for part in re.split(r"\s{2,}", text):
            part = part.strip()
            if part:
                self.items.append(part)


def norm(text):
    return (text or "").replace("臺", "台").strip()


def clean_addr(text):
    return re.sub(r"^\s*\d{3,6}\s*", "", norm(text))


def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read().decode("utf-8", "replace")


def visible_items(markup):
    parser = TextParser()
    parser.feed(markup)
    out = []
    skip = {
        "門市資訊", "服飾", "餐飲", "口罩", "可刷卡", "line pay電子支付", "國民旅遊卡特約商店",
        "外帶專賣店", "所有門市", "請選擇地區", "FACEBOOK", "INSTAGRAM", "LINE", "公司簡介",
        "購物說明", "隱私權政策", "防詐騙宣導", "人才招募", "廠商合作", "品牌公益", "會員專區",
        "WHAT'S NEWS", "聯絡我們", "Loading..", "x close", "登入", "註冊", "聯名", "WOMEN", "MEN",
        "KIDS", "NAVY", "SALE", "周邊",
    }
    for item in parser.items:
        item = item.strip(" |")
        if not item or item in skip:
            continue
        if re.fullmatch(r"\d+", item):
            continue
        out.append(item)
    return out


def looks_like_addr(text):
    text = clean_addr(text)
    return bool(CITY_RE.search(text) and re.search(r"[區鄉鎮市].*[路街道段巷弄號]|[路街道段巷弄號]", text))


def looks_like_store_title(text, kind):
    text = norm(text)
    if not text or looks_like_addr(text):
        return False
    if re.search(r"門市電話|活動時間|週[一二三四五六日]|Mon-Fri|統一編號|搶先訂閱|可刷卡", text):
        return False
    if kind == "CAFE":
        return text.lower().startswith("caco cafe")
    return "快閃" in text and bool(re.search(r"[（(][^）)]+[）)]", text))


def parse_records(markup, kind):
    items = visible_items(markup)
    records = []
    current = None
    for item in items:
        item = norm(item)
        if looks_like_store_title(item, kind):
            current = {"title": item, "addr": "", "end": "", "source": CAFE_URL if kind == "CAFE" else POPUP_URL}
            records.append(current)
            continue
        if not current:
            continue
        if not current["addr"] and looks_like_addr(item):
            current["addr"] = clean_addr(item)
            continue
        if kind == "POPUP" and not current["end"] and "活動時間至" in item:
            current["end"] = parse_end(item)
    return [r for r in records if r.get("addr")]


def parse_end(text):
    text = norm(text)
    m = re.search(r"(\d{4})/(\d{1,2})/(\d{1,2})", text)
    if m:
        return f"{int(m.group(1)):04d}/{int(m.group(2)):02d}/{int(m.group(3)):02d}"
    m = re.search(r"(\d{4})/(\d{1,2})月", text)
    if m:
        year, month = int(m.group(1)), int(m.group(2))
        # Month-only dates are kept until the month's last common day; refresh will filter past end.
        if month == 12:
            day = 31
        else:
            day = (datetime.date(year, month + 1, 1) - datetime.timedelta(days=1)).day
        return f"{year:04d}/{month:02d}/{day:02d}"
    return ""


def popup_event_title(title):
    m = re.search(r"[（(]([^）)]+)[）)]", title)
    ip = m.group(1).strip() if m else "CACO 快閃"
    return f"CACO {ip}"


def build_extra(popups):
    out = {}
    for item in popups:
        name = item["title"]
        out[name] = {
            "addr": item["addr"],
            "url": POPUP_URL,
            "ex": [{
                "t": popup_event_title(name),
                "s": "",
                "e": item.get("end", ""),
                "l": POPUP_URL,
                "img": "",
            }],
        }
    return out


def main():
    cafe_html = fetch(CAFE_URL)
    popup_html = fetch(POPUP_URL)
    cafes = parse_records(cafe_html, "CAFE")
    popups = parse_records(popup_html, "POPUP")
    json.dump({
        "_note": "Generated from official CACO storelist pages.",
        "cafe_url": CAFE_URL,
        "popup_url": POPUP_URL,
        "cafes": cafes,
        "popups": popups,
    }, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    extra = build_extra(popups)
    json.dump({
        "_note": "ACG-related CACO popup events generated from caco_stores.json.",
        "venues": extra,
    }, open(EXTRA, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(json.dumps({"cafes": len(cafes), "acg_popups": len(popups)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
