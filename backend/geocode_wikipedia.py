#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Add coordinate overrides from Chinese Wikipedia page coordinates."""
import json, os, urllib.parse, urllib.request
from paths import path as P

HERE = os.path.dirname(os.path.abspath(__file__))
VENUES = P("venues.json")
OUT = P("venue_geocodes.json")
UA = "tw-exhibition-map/0.1 local maintenance"

def chunks(xs, n):
    for i in range(0, len(xs), n):
        yield xs[i:i+n]

def main():
    venues = [v for v in json.load(open(VENUES, encoding="utf-8"))["venues"] if v.get("loc") != "exact"]
    accepted = json.load(open(OUT, encoding="utf-8")) if os.path.exists(OUT) else {}
    names = [v["name"] for v in venues if v["name"] not in accepted and v["name"] != "未具名場地"]
    added = 0
    for batch in chunks(names, 40):
        url = "https://zh.wikipedia.org/w/api.php?" + urllib.parse.urlencode({
            "action": "query",
            "titles": "|".join(batch),
            "prop": "coordinates",
            "redirects": "1",
            "format": "json",
            "colimit": "max",
        })
        req = urllib.request.Request(url, headers={"User-Agent": UA})
        data = json.loads(urllib.request.urlopen(req, timeout=25).read().decode("utf-8"))
        pages = data.get("query", {}).get("pages", {})
        for page in pages.values():
            title = page.get("title")
            coords = page.get("coordinates") or []
            if not title or title not in names or not coords:
                continue
            c = coords[0]
            accepted[title] = {
                "la": round(float(c["lat"]), 7),
                "lo": round(float(c["lon"]), 7),
                "source": "zh_wikipedia",
                "display_name": title,
                "type": "wiki_page",
            }
            print("OK", title, accepted[title]["la"], accepted[title]["lo"])
            added += 1
        json.dump(accepted, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(json.dumps({"added": added, "accepted_total": len(accepted)}, ensure_ascii=False))

if __name__ == "__main__":
    main()
