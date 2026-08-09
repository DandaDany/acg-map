#!/usr/bin/env python3
"""One-time/repeatable Git-history backfill for data/event_first_seen.json."""

from __future__ import annotations

import json
import subprocess
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from event_first_seen import load_registry
from refresh_venues import event_group_id


ROOT = Path(__file__).resolve().parent.parent
REGISTRY = ROOT / "data" / "event_first_seen.json"
TAIPEI = ZoneInfo("Asia/Taipei")


def git(*args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=ROOT, text=True, stderr=subprocess.DEVNULL)


def backfill() -> dict[str, str | None]:
    registry = load_registry(REGISTRY)
    commits = git("rev-list", "--reverse", "--all", "--", "public/venues.json").splitlines()
    for commit in commits:
        try:
            raw = git("show", f"{commit}:public/venues.json")
            payload = json.loads(raw)
            stamp = git("show", "-s", "--format=%cI", commit).strip()
            seen_date = datetime.fromisoformat(stamp).astimezone(TAIPEI).date().isoformat()
        except (subprocess.CalledProcessError, json.JSONDecodeError, ValueError):
            continue
        for venue in payload.get("venues", []):
            for event in venue.get("ex", []):
                if event.get("c") != "ACG":
                    continue
                event_id = event_group_id(event)
                old = registry.get(event_id)
                if old is None or seen_date < old:
                    registry[event_id] = seen_date

    # Current IDs not recoverable from any parseable historical public snapshot stay null.
    current = json.loads((ROOT / "public" / "venues.json").read_text(encoding="utf-8"))
    for venue in current.get("venues", []):
        for event in venue.get("ex", []):
            if event.get("c") == "ACG" and event.get("id"):
                registry.setdefault(event["id"], None)

    REGISTRY.write_text(json.dumps(dict(sorted(registry.items())), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return registry


if __name__ == "__main__":
    result = backfill()
    known = sum(value is not None for value in result.values())
    print(f"event_first_seen: {known} dated, {len(result) - known} null")
