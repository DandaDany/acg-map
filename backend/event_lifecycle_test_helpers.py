"""Helpers for regression tests that inspect the dated public map snapshot."""
from datetime import datetime


def parse_date(value):
    text = str(value or "").strip().split(" ", 1)[0].replace("-", "/")
    return datetime.strptime(text, "%Y/%m/%d").date() if text else None


def snapshot_date(public):
    """Use the generated snapshot date, never the wall-clock date of CI."""
    value = parse_date(public.get("updated"))
    if value is None:
        raise AssertionError("public/venues.json is missing its updated snapshot date")
    return value


def manual_rows(events, title):
    return [
        row
        for row in events
        if row.get("活動名稱 / Activity Name") == title
    ]


def active_manual_rows(public, events, title):
    as_of = snapshot_date(public)
    return [
        row
        for row in manual_rows(events, title)
        if parse_date(row.get("結束日期 / End Date")) is None
        or parse_date(row.get("結束日期 / End Date")) >= as_of
    ]


def public_pins(public, title):
    return [
        (venue, event)
        for venue in public["venues"]
        for event in venue.get("ex", [])
        if event.get("t") == title
    ]


def venue_name(row):
    return str(row.get("地點 / Location") or "").split("（", 1)[0]


def assert_public_matches_lifecycle(
    testcase,
    public,
    events,
    title,
    *,
    active_count=None,
    active_venues=None,
):
    """Assert live pins only for rows active on the generated snapshot date."""
    active = active_manual_rows(public, events, title)
    pins = public_pins(public, title)
    expected_count = (active_count if active_count is not None else len(active)) if active else 0
    testcase.assertEqual(len(pins), expected_count, title)
    if active_venues is not None:
        expected_venues = set(active_venues) if active else set()
    elif active_count is None:
        expected_venues = {venue_name(row) for row in active}
    else:
        expected_venues = None
    if expected_venues is not None:
        testcase.assertEqual(
            {venue["name"] for venue, _ in pins},
            expected_venues,
            title,
        )
    return pins
