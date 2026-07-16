#!/usr/bin/env python3
import io
from paths import path as P
import json
import re


def sync_html():
    data = json.load(open(P("venues.json"), encoding="utf-8"))
    path = P("taiwan-exhibition-map.html")
    lines = io.open(path, encoding="utf-8").readlines()
    line = (
        "let DATA = "
        + json.dumps(data, ensure_ascii=False, separators=(",", ":"))
        + "; let liveMode=false;\n"
    )
    hits = 0
    for i, current in enumerate(lines):
        if current.lstrip().startswith("let DATA = ") and "let liveMode=false;" in current:
            lines[i] = line
            hits += 1
    assert hits == 1, hits
    io.open(path, "w", encoding="utf-8").writelines(lines)
    return hits


def build_report():
    venues = json.load(open(P("venues.json"), encoding="utf-8"))["venues"]
    full = []
    partial = []
    for venue in venues:
        if venue.get("loc") == "exact":
            continue
        addr = venue.get("addr", "")
        (full if re.search(r"[路街道段巷弄號]", addr) else partial).append(venue)
    report = {
        "summary": {
            "venues_total": len(venues),
            "exact": sum(1 for venue in venues if venue.get("loc") == "exact"),
            "approx_total": len(full) + len(partial),
            "has_road_or_addr": len(full),
            "only_area": len(partial),
        },
        "has_road_or_addr": [
            {key: venue.get(key, "") for key in ["name", "city", "addr", "loc", "url"]}
            for venue in full
        ],
        "only_area": [
            {key: venue.get(key, "") for key in ["name", "city", "addr", "loc", "url"]}
            for venue in partial
        ],
    }
    json.dump(
        report,
        open("_approx_location_report.json", "w", encoding="utf-8"),
        ensure_ascii=False,
        indent=1,
    )
    return report


def main():
    print("synced", sync_html())
    report = build_report()
    print(report["summary"])
    print("HAS_ROAD")
    for item in report["has_road_or_addr"]:
        print(item["name"], "|", item["addr"])
    print("ONLY_AREA")
    for item in report["only_area"]:
        print(item["name"], "|", item["addr"])


if __name__ == "__main__":
    main()
