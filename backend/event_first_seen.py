#!/usr/bin/env python3
"""Persistent first-seen dates for public ACG activity group IDs."""

from __future__ import annotations

import datetime as dt
import json
from pathlib import Path
from zoneinfo import ZoneInfo


TAIPEI = ZoneInfo("Asia/Taipei")


def taipei_today() -> str:
    return dt.datetime.now(TAIPEI).date().isoformat()


def load_registry(path: Path) -> dict[str, str | None]:
    if not path.exists():
        return {}
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("event_first_seen registry must be a JSON object")
    return {str(key): value for key, value in data.items() if value is None or isinstance(value, str)}


def apply_first_seen(venues: list[dict], registry_path: Path, today: str | None = None) -> dict[str, str | None]:
    """Keep existing dates, register new stable IDs, and expose first_seen publicly."""
    registry = load_registry(registry_path)
    today = today or taipei_today()
    changed = False
    for venue in venues:
        for event in venue.get("ex", []):
            event_id = str(event.get("id") or "").strip()
            if event.get("c") != "ACG" or not event_id:
                continue
            if event_id not in registry:
                registry[event_id] = today
                changed = True
            event["first_seen"] = registry[event_id]
    if changed or not registry_path.exists():
        registry_path.parent.mkdir(parents=True, exist_ok=True)
        registry_path.write_text(
            json.dumps(dict(sorted(registry.items())), ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
    return registry
