#!/usr/bin/env python3
import json
from paths import path as P
import sys

import geocode_venues as g


def main():
    cache = json.load(open(P("geocode_cache.json"), encoding="utf-8"))
    for q in sys.argv[1:]:
        print("---", q)
        try:
            results = g.search(q, cache)
        except Exception as e:
            print("ERR", type(e).__name__, str(e)[:200])
            results = []
        for r in results[:5]:
            print(
                r.get("display_name"),
                r.get("lat"),
                r.get("lon"),
                r.get("class"),
                r.get("type"),
            )


if __name__ == "__main__":
    main()
