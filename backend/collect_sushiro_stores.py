#!/usr/bin/env python3
"""Collect Taiwan Sushiro stores and their official Google Maps pins.

The Sushiro store detail page embeds a Google Maps query for each named store.
This collector follows that first-party query and records the coordinate returned
by Google Maps, so the result is reproducible without browser-coordinate clicking.

The JOJO collaboration explicitly excludes the take-out-only TOGO store.  The
generated reference file therefore keeps that store in ``排除門市`` and exposes
only participating dine-in stores through ``門市清單``.
"""

from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
import html
import json
from pathlib import Path
import re
import time
from urllib.parse import quote, unquote, urlsplit, urlunsplit
from urllib.request import Request, urlopen


ROOT = Path(__file__).resolve().parents[1]
SHOP_LIST_URL = "https://www.sushiro.com.tw/Shop"
SHOP_LIST_API = "https://www.sushiro.com.tw/Shop/_ShopList"
SHOP_DETAIL = "https://www.sushiro.com.tw/Shop/ShopInfo?shopId={}"
OUTPUT = ROOT / "data" / "manual" / "台灣壽司郎門市地址_20260815.json"
GEOCODES = ROOT / "data" / "manual" / "address_geocodes.json"
VENUE_GEOCODES = ROOT / "data" / "manual" / "venue_geocodes.json"
USER_AGENT = "Mozilla/5.0 (compatible; acg-map-maintenance/1.0)"


def fetch(url: str, data: bytes | None = None, attempts: int = 3) -> str:
    parts = urlsplit(url)
    url = urlunsplit(
        (parts.scheme, parts.netloc, quote(unquote(parts.path), safe="/%"),
         quote(unquote(parts.query), safe="=&%"), parts.fragment)
    )
    last_error = None
    for attempt in range(attempts):
        try:
            req = Request(url, data=data, headers={"User-Agent": USER_AGENT})
            with urlopen(req, timeout=30) as response:
                return response.read().decode("utf-8", errors="replace")
        except Exception as exc:  # pragma: no cover - network recovery
            last_error = exc
            if attempt + 1 < attempts:
                time.sleep(1.5 * (attempt + 1))
    raise RuntimeError(f"fetch failed after {attempts} attempts: {url}: {last_error}")


def clean_text(value: str) -> str:
    value = html.unescape(re.sub(r"<[^>]+>", "", value))
    return re.sub(r"\s+", " ", value).strip()


def clean_address(value: str) -> str:
    value = clean_text(value).replace("臺", "台")
    value = value.translate(str.maketrans("０１２３４５６７８９", "0123456789"))
    value = re.sub(r"^\d{3}(?:-\d{2,3})?\s*", "", value)
    return value.strip()


def geocode_key(value: str) -> str:
    value = clean_address(value)
    value = re.sub(r"\s+", "", value)
    return re.sub(r"[，,].*$", "", value)


def parse_store_list(page: str) -> list[dict]:
    pattern = re.compile(
        r'<a href="/Shop/ShopInfo\?shopId=(\d+)">.*?'
        r"<h3>(.*?)</h3>.*?<p>.*?</p>.*?"
        r'<p class="inner-border-box-font-content mt-0">(.*?)</p>',
        re.S,
    )
    stores = []
    for shop_id, name, address in pattern.findall(page):
        stores.append(
            {
                "shop_id": int(shop_id),
                "門市名稱": clean_text(name),
                "地址": clean_address(address),
                "官方門市頁": SHOP_DETAIL.format(shop_id),
            }
        )
    if not stores:
        raise RuntimeError("official Sushiro store list returned no stores")
    return stores


def official_map_url(detail_page: str) -> str:
    match = re.search(r'<iframe[^>]+class="google-map"[^>]+src="([^"]+)"', detail_page, re.S)
    if not match:
        match = re.search(r'<iframe[^>]+src="([^"]*google\.com/maps[^"]+)"', detail_page, re.S)
    if not match:
        raise RuntimeError("store detail page has no Google Maps iframe")
    return html.unescape(match.group(1))


def map_pin(map_page: str) -> tuple[float, float]:
    # The Maps embed response carries the selected place coordinate as a plain
    # latitude/longitude pair even when the surrounding payload is minified.
    matches = re.findall(r"(2[1-6]\.\d{5,}),\s*(11[89]|12[0-2])\.(\d{5,})", map_page)
    if not matches:
        raise RuntimeError("Google Maps embed response has no Taiwan coordinate")
    # When Google includes both viewport metadata and the selected place, the
    # selected-place coordinate is the final Taiwan pair in the response.
    lat, lng_head, lng_tail = matches[-1]
    return float(lat), float(f"{lng_head}.{lng_tail}")


def enrich(store: dict, cached: dict | None = None) -> dict:
    try:
        detail = fetch(store["官方門市頁"])
        map_url = official_map_url(detail)
        last_error = None
        for attempt in range(4):
            try:
                lat, lng = map_pin(fetch(map_url))
                break
            except RuntimeError as exc:
                last_error = exc
                time.sleep(2 * (attempt + 1))
        else:
            raise last_error
    except Exception as exc:
        if cached and cached.get("地址") == store["地址"]:
            result = dict(store)
            result.update({key: cached[key] for key in ("緯度", "經度", "座標來源", "Google Maps 查詢")})
            return result
        raise RuntimeError(f'{store["門市名稱"]} (shopId={store["shop_id"]}): {exc}') from exc
    result = dict(store)
    result.update(
        {
            "緯度": lat,
            "經度": lng,
            "座標來源": "Google Maps 店名圖釘（由台灣壽司郎官方門市頁嵌入查詢）",
            "Google Maps 查詢": unquote(map_url),
        }
    )
    return result


def collect() -> list[dict]:
    stores = parse_store_list(fetch(SHOP_LIST_API, data=b"data=||"))
    cache = {}
    if OUTPUT.exists():
        try:
            old = json.loads(OUTPUT.read_text(encoding="utf-8"))
            for item in old.get("門市清單", []) + old.get("排除門市", []):
                cache[item.get("shop_id")] = item
        except Exception:
            cache = {}
    enriched = [None] * len(stores)
    with ThreadPoolExecutor(max_workers=4) as executor:
        pending = {executor.submit(enrich, store, cache.get(store["shop_id"])): i for i, store in enumerate(stores)}
        for future in as_completed(pending):
            enriched[pending[future]] = future.result()
    return enriched


def write_payload(stores: list[dict], output: Path, write_geocodes: bool) -> None:
    excluded = [store for store in stores if store["門市名稱"].lower().startswith("to go")]
    participating = [store for store in stores if store not in excluded]
    payload = {
        "_說明": "台灣壽司郎官方門市與 Google Maps 精確店名圖釘，供多店聯名活動展開。",
        "來源": SHOP_LIST_URL,
        "查詢時間": "2026-08-15",
        "官網全部店舖數": len(stores),
        "JOJO活動參與門市數": len(participating),
        "座標方法": "逐店讀取官方門市詳細頁內嵌 Google Maps 查詢，再擷取該店名圖釘座標；非地址質心。",
        "活動範圍來源": "https://www.facebook.com/Sushiro.TW/posts/1485367983629113/",
        "活動排除規則": "官方貼文載明活動僅限內用，不適用外帶、外送及 TOGO 店。",
        "排除門市": excluded,
        "門市清單": participating,
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    if write_geocodes:
        geocodes = json.loads(GEOCODES.read_text(encoding="utf-8"))
        geocodes = {
            key: value for key, value in geocodes.items()
            if value.get("source") != "google_maps_official_sushiro_store_pin_2026-08-15"
        }
        for store in participating:
            geocodes[geocode_key(store["地址"])] = {
                "la": store["緯度"],
                "lo": store["經度"],
                "source": "google_maps_official_sushiro_store_pin_2026-08-15",
                "display_name": f'台灣壽司郎 {store["門市名稱"]}（{store["地址"]}）',
                "type": "official_store_google_maps_pin",
                "score": 100,
            }
        GEOCODES.write_text(json.dumps(geocodes, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")

        venue_geocodes = json.loads(VENUE_GEOCODES.read_text(encoding="utf-8"))
        venue_geocodes = {
            key: value for key, value in venue_geocodes.items()
            if value.get("source") != "google_maps_official_sushiro_store_pin_2026-08-15"
        }
        for store in participating:
            venue_geocodes[f'台灣壽司郎 {store["門市名稱"]}'] = {
                "la": store["緯度"],
                "lo": store["經度"],
                "source": "google_maps_official_sushiro_store_pin_2026-08-15",
                "display_name": f'台灣壽司郎 {store["門市名稱"]}（{store["地址"]}）',
                "type": "official_store_google_maps_pin",
                "addr_key": geocode_key(store["地址"]),
                "loc": "exact",
                "precision_note": "台灣壽司郎官方門市頁內嵌 Google Maps 店名圖釘",
            }
        VENUE_GEOCODES.write_text(
            json.dumps(venue_geocodes, ensure_ascii=False, indent=1) + "\n", encoding="utf-8"
        )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=OUTPUT)
    parser.add_argument("--write-geocodes", action="store_true")
    args = parser.parse_args()
    stores = collect()
    write_payload(stores, args.output, args.write_geocodes)
    print(f"stores={len(stores)} participating={sum(not s['門市名稱'].lower().startswith('to go') for s in stores)} output={args.output}")


if __name__ == "__main__":
    main()
