#!/usr/bin/env python3
import json
from paths import path as P
import sys

import geocode_venues as g


def main():
    cache = json.load(open(P("arcgis_geocode_cache.json"), encoding="utf-8"))
    for q in sys.argv[1:]:
        print("---", q)
        try:
            data = g.search_arcgis(q, cache)
        except Exception as e:
            print("ERR", type(e).__name__, str(e)[:200])
            continue
        for cand in data.get("candidates", [])[:5]:
            print(json.dumps(cand, ensure_ascii=False))


if __name__ == "__main__":
    main()
