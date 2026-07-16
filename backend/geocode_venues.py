#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Batch geocode approximate venues with known addresses.

This uses conservative OpenStreetMap Nominatim POI lookup as a quick first pass:
only results whose display name contains the venue name and whose type is not a
transit/parking object are accepted. Misses are left unchanged.

Outputs:
  geocode_cache.json   raw query cache
  venue_geocodes.json  accepted venue -> exact coordinate overrides
  address_geocodes.json accepted normalized address -> exact coordinate overrides
"""
import json, os, re, time, urllib.parse, urllib.request
from paths import path as P

HERE = os.path.dirname(os.path.abspath(__file__))
VENUES = P("venues.json")
CACHE = P("geocode_cache.json")
ARCGIS_CACHE = P("arcgis_geocode_cache.json")
OUT = P("venue_geocodes.json")
ADDR_OUT = P("address_geocodes.json")

USER_AGENT = "tw-exhibition-map-geocode/0.1 (local maintenance)"
BAD_TYPES = {"administrative", "bicycle_rental", "bus_stop", "government", "parking", "platform", "social_facility", "station", "stop", "yes"}
GOOD_HINTS = re.compile(r"art|museum|gallery|arts|centre|center|attraction|industrial|building|cultural|community|commercial|park|square", re.I)
CITY = r"(台北市|臺北市|新北市|桃園市|台中市|臺中市|台南市|臺南市|高雄市|基隆市|新竹市|新竹縣|苗栗縣|彰化縣|南投縣|雲林縣|嘉義市|嘉義縣|屏東縣|宜蘭縣|花蓮縣|台東縣|臺東縣|澎湖縣|金門縣|連江縣)"
CITY_RE = re.compile(CITY)
CITY_BOUNDS = {
    '台北市': (24.9, 25.25, 121.43, 121.68), '新北市': (24.65, 25.35, 121.25, 122.05),
    '基隆市': (25.05, 25.2, 121.65, 121.85), '桃園市': (24.55, 25.15, 120.95, 121.5),
    '新竹市': (24.72, 24.88, 120.88, 121.05), '新竹縣': (24.35, 24.95, 120.9, 121.35),
    '苗栗縣': (24.25, 24.75, 120.55, 121.2), '台中市': (23.95, 24.45, 120.45, 121.45),
    '彰化縣': (23.78, 24.18, 120.25, 120.65), '南投縣': (23.45, 24.35, 120.55, 121.35),
    '雲林縣': (23.45, 23.9, 120.1, 120.75), '嘉義市': (23.43, 23.53, 120.38, 120.5),
    '嘉義縣': (23.2, 23.65, 120.1, 120.8), '台南市': (22.85, 23.45, 120.0, 120.65),
    '高雄市': (22.45, 23.35, 120.15, 121.05), '屏東縣': (21.85, 22.9, 120.4, 120.95),
    '宜蘭縣': (24.25, 25.05, 121.45, 122.05), '花蓮縣': (23.0, 24.4, 121.1, 121.8),
    '台東縣': (21.9, 23.5, 120.7, 121.6), '澎湖縣': (23.1, 23.9, 119.2, 119.8),
    '金門縣': (24.35, 24.55, 118.1, 118.55), '連江縣': (25.9, 26.4, 119.8, 120.6),
}

def norm(s):
    s = (s or "").replace("臺", "台").lower()
    return "".join(ch for ch in s if ch.isalnum())

def clean_addr(addr):
    addr = (addr or "").replace("臺", "台").strip()
    addr = re.sub(r"^\s*\d{3,6}\s*", "", addr)
    addr = re.sub(r"\s+", "", addr)
    addr = re.sub(r"[，,].*$", "", addr)
    return addr

def city_of(addr):
    m = CITY_RE.search(addr or "")
    return (m.group(1) if m else "").replace("臺", "台")

def full_addr(addr):
    return bool(re.search(r"[路街道段巷弄].*號", clean_addr(addr)))

def coord_matches_city(city, la, lo):
    b = CITY_BOUNDS.get((city or "").replace("臺", "台"))
    if not b:
        return True
    return b[0] <= float(la) <= b[1] and b[2] <= float(lo) <= b[3]

def key_parts(name):
    n = norm(name)
    parts = [n]
    for cut in ("文化創意產業園區", "文化園區", "藝術中心", "美術館", "博物館", "藝文特區"):
        if cut in name:
            parts.append(norm(name.replace(cut, "")))
    return [p for p in parts if len(p) >= 3]

def result_ok(name, result):
    disp = norm(result.get("display_name", ""))
    if not any(p in disp for p in key_parts(name)):
        return False
    typ = (result.get("type") or "").lower()
    if typ in BAD_TYPES:
        return False
    cls = (result.get("class") or "").lower()
    if cls in {"railway", "highway", "amenity"} and typ in BAD_TYPES:
        return False
    return bool(GOOD_HINTS.search(typ) or GOOD_HINTS.search(cls))

def address_result_ok(addr, result):
    la, lo = float(result.get("lat", 0)), float(result.get("lon", 0))
    city = city_of(addr)
    if city and not coord_matches_city(city, la, lo):
        return False
    disp = norm(result.get("display_name", ""))
    key = norm(clean_addr(addr))
    if len(key) >= 8 and key[:8] in disp:
        return True
    typ = (result.get("type") or "").lower()
    cls = (result.get("class") or "").lower()
    return typ in {"house", "building", "apartments", "commercial", "yes"} or cls in {"building", "shop", "tourism", "amenity"}

def search(query, cache):
    if query in cache:
        return cache[query]
    url = "https://nominatim.openstreetmap.org/search?" + urllib.parse.urlencode({
        "format": "jsonv2",
        "q": query,
        "limit": 5,
        "countrycodes": "tw",
    })
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=25) as r:
        data = json.loads(r.read().decode("utf-8"))
    cache[query] = data
    json.dump(cache, open(CACHE, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    time.sleep(1.1)
    return data

def search_arcgis(addr, cache):
    if addr in cache:
        return cache[addr]
    url = "https://geocode.arcgis.com/arcgis/rest/services/World/GeocodeServer/findAddressCandidates?" + urllib.parse.urlencode({
        "SingleLine": addr,
        "f": "json",
        "countryCode": "TWN",
        "maxLocations": 3,
        "outFields": "Match_addr,Addr_type,Score",
    })
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=25) as r:
        data = json.loads(r.read().decode("utf-8"))
    cache[addr] = data
    json.dump(cache, open(ARCGIS_CACHE, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    time.sleep(0.3)
    return data

def arcgis_address_result(addr, data):
    city = city_of(addr)
    for cand in data.get("candidates", []):
        loc = cand.get("location") or {}
        score = float(cand.get("score") or cand.get("attributes", {}).get("Score") or 0)
        addr_type = (cand.get("attributes", {}).get("Addr_type") or "").lower()
        la, lo = loc.get("y"), loc.get("x")
        if la is None or lo is None or score < 88:
            continue
        if city and not coord_matches_city(city, la, lo):
            continue
        if addr_type and addr_type not in {"pointaddress", "streetaddress", "streetaddressext", "streetint", "streetname", "locality"}:
            continue
        return cand
    return None

def arcgis_poi_result(name, city, data):
    for cand in data.get("candidates", []):
        loc = cand.get("location") or {}
        score = float(cand.get("score") or cand.get("attributes", {}).get("Score") or 0)
        addr_type = (cand.get("attributes", {}).get("Addr_type") or "").lower()
        la, lo = loc.get("y"), loc.get("x")
        if la is None or lo is None or score < 95:
            continue
        if city and not coord_matches_city(city, la, lo):
            continue
        if addr_type not in {"poi", "pointaddress", "streetaddress", "streetaddressext"}:
            continue
        disp = norm(cand.get("address", ""))
        if norm(name)[:3] and norm(name)[:3] not in disp:
            continue
        return cand
    return None

def main():
    data = json.load(open(VENUES, encoding="utf-8"))
    venues = data.get("venues", [])
    cache = json.load(open(CACHE, encoding="utf-8")) if os.path.exists(CACHE) else {}
    arcgis_cache = json.load(open(ARCGIS_CACHE, encoding="utf-8")) if os.path.exists(ARCGIS_CACHE) else {}
    accepted = json.load(open(OUT, encoding="utf-8")) if os.path.exists(OUT) else {}
    accepted_addr = json.load(open(ADDR_OUT, encoding="utf-8")) if os.path.exists(ADDR_OUT) else {}

    targets = [v for v in venues if v.get("loc") != "exact" and v.get("addr")]
    ok = addr_ok = miss = 0
    for v in targets:
        if v["name"] in accepted:
            continue
        addr_key = clean_addr(v.get("addr", ""))
        has_full_addr = full_addr(addr_key)
        if full_addr(addr_key) and addr_key not in accepted_addr:
            chosen_addr = None
            try:
                chosen_arcgis = arcgis_address_result(addr_key, search_arcgis(addr_key, arcgis_cache))
            except Exception as e:
                print("ERR", v["name"], "ArcGIS", type(e).__name__, str(e)[:80], flush=True)
                chosen_arcgis = None
            if chosen_arcgis:
                loc = chosen_arcgis["location"]
                accepted_addr[addr_key] = {
                    "la": round(float(loc["y"]), 7),
                    "lo": round(float(loc["x"]), 7),
                    "source": "arcgis_address",
                    "display_name": chosen_arcgis.get("address", ""),
                    "type": chosen_arcgis.get("attributes", {}).get("Addr_type", ""),
                    "score": chosen_arcgis.get("score", chosen_arcgis.get("attributes", {}).get("Score", "")),
                }
                json.dump(accepted_addr, open(ADDR_OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
                addr_ok += 1
                print("ADDR", v["name"], accepted_addr[addr_key]["la"], accepted_addr[addr_key]["lo"], addr_key, flush=True)
            for q in ([] if addr_key in accepted_addr else [f"{addr_key} 台灣", f"{v.get('name','')} {addr_key} 台灣"]):
                try:
                    results = search(q, cache)
                except Exception as e:
                    print("ERR", v["name"], type(e).__name__, str(e)[:80], flush=True)
                    results = []
                for r in results:
                    if address_result_ok(addr_key, r):
                        chosen_addr = r
                        break
                if chosen_addr:
                    break
            if chosen_addr:
                accepted_addr[addr_key] = {
                    "la": round(float(chosen_addr["lat"]), 7),
                    "lo": round(float(chosen_addr["lon"]), 7),
                    "source": "nominatim_address",
                    "display_name": chosen_addr.get("display_name", ""),
                    "type": chosen_addr.get("type", ""),
                }
                json.dump(accepted_addr, open(ADDR_OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
                addr_ok += 1
                print("ADDR", v["name"], accepted_addr[addr_key]["la"], accepted_addr[addr_key]["lo"], addr_key, flush=True)
        if addr_key in accepted_addr:
            g = accepted_addr[addr_key]
            accepted[v["name"]] = {
                "la": g["la"],
                "lo": g["lo"],
                "source": "address_geocode",
                "display_name": g.get("display_name", ""),
                "type": g.get("type", ""),
                "addr_key": addr_key,
            }
            json.dump(accepted, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
            print("OK", v["name"], accepted[v["name"]]["la"], accepted[v["name"]]["lo"], "address", flush=True)
            ok += 1
            continue
        if not has_full_addr:
            try:
                q = f"{v['name']} {v.get('city','')} 台灣"
                chosen_poi = arcgis_poi_result(v["name"], v.get("city", ""), search_arcgis(q, arcgis_cache))
            except Exception as e:
                print("ERR", v["name"], "ArcGISPOI", type(e).__name__, str(e)[:80], flush=True)
                chosen_poi = None
            if chosen_poi:
                loc = chosen_poi["location"]
                accepted[v["name"]] = {
                    "la": round(float(loc["y"]), 7),
                    "lo": round(float(loc["x"]), 7),
                    "source": "arcgis_poi",
                    "display_name": chosen_poi.get("address", ""),
                    "type": chosen_poi.get("attributes", {}).get("Addr_type", ""),
                    "score": chosen_poi.get("score", chosen_poi.get("attributes", {}).get("Score", "")),
                }
                json.dump(accepted, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
                print("OK", v["name"], accepted[v["name"]]["la"], accepted[v["name"]]["lo"], "arcgis_poi", flush=True)
                ok += 1
                continue
            print("SKIP_PARTIAL", v["name"], flush=True)
            miss += 1
            continue
        queries = [
            f"{v['name']} {v.get('city','')} 台灣",
            f"{v['name']} {v.get('addr','')} 台灣",
        ]
        chosen = None
        for q in queries:
            try:
                results = search(q, cache)
            except Exception as e:
                print("ERR", v["name"], type(e).__name__, str(e)[:80], flush=True)
                results = []
            for r in results:
                if result_ok(v["name"], r):
                    chosen = r
                    break
            if chosen:
                break
        if chosen:
            accepted[v["name"]] = {
                "la": round(float(chosen["lat"]), 7),
                "lo": round(float(chosen["lon"]), 7),
                "source": "nominatim_poi",
                "display_name": chosen.get("display_name", ""),
                "type": chosen.get("type", ""),
            }
            json.dump(accepted, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
            print("OK", v["name"], accepted[v["name"]]["la"], accepted[v["name"]]["lo"], chosen.get("type", ""), flush=True)
            ok += 1
        else:
            print("MISS", v["name"], flush=True)
            miss += 1
    print(json.dumps({"targets": len(targets), "accepted_total": len(accepted), "address_total": len(accepted_addr), "accepted_this_run": ok, "address_this_run": addr_ok, "miss_this_run": miss}, ensure_ascii=False))

if __name__ == "__main__":
    main()
