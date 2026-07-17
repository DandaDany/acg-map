#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Central project paths for the future backend layout."""
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent
ROOT = BACKEND_DIR.parent

PUBLIC_DIR = ROOT / "public"
DATA_DIR = ROOT / "data"
MANUAL_DIR = DATA_DIR / "manual"
GENERATED_DIR = DATA_DIR / "generated"
CACHE_DIR = DATA_DIR / "cache"
LOGO_DATA_DIR = DATA_DIR / "logos"
REFERENCE_DIR = DATA_DIR / "reference"
REPORTS_DIR = DATA_DIR / "reports"
DOCS_DIR = ROOT / "docs"
OPS_DIR = ROOT / "ops"
ARCHIVE_DIR = ROOT / "archive"
RUNTIME_DIR = ROOT / "runtime"

PUBLIC_VENUES = PUBLIC_DIR / "venues.json"
PUBLIC_MAP_HTML = PUBLIC_DIR / "taiwan-exhibition-map.html"
PUBLIC_LOGOS_DIR = PUBLIC_DIR / "logos"

_FILES = {
    # Public static app
    "venues.json": PUBLIC_VENUES,
    "taiwan-exhibition-map.html": PUBLIC_MAP_HTML,
    "logos": PUBLIC_LOGOS_DIR,

    # Manual / editorial data
    "全台ACG活動.xlsx": MANUAL_DIR / "全台ACG活動.xlsx",
    "acg_events.json": MANUAL_DIR / "acg_events.json",
    "review_decisions.json": MANUAL_DIR / "review_decisions.json",
    "manual_extra.json": MANUAL_DIR / "manual_extra.json",
    "manual_permanent_extra.json": MANUAL_DIR / "manual_permanent_extra.json",
    "venue_corrections.json": MANUAL_DIR / "venue_corrections.json",
    "venue_address_overrides.json": MANUAL_DIR / "venue_address_overrides.json",
    "event_link_overrides.json": MANUAL_DIR / "event_link_overrides.json",
    "event_overrides.json": MANUAL_DIR / "event_overrides.json",
    "venue_event_sources.json": MANUAL_DIR / "venue_event_sources.json",
    "venue_geocodes.json": MANUAL_DIR / "venue_geocodes.json",
    "address_geocodes.json": MANUAL_DIR / "address_geocodes.json",

    # Generated pipeline data
    "venue_extra.json": GENERATED_DIR / "venue_extra.json",
    "soka_extra.json": GENERATED_DIR / "soka_extra.json",
    "caco_extra.json": GENERATED_DIR / "caco_extra.json",
    "caco_stores.json": GENERATED_DIR / "caco_stores.json",
    "cayenne_extra.json": GENERATED_DIR / "cayenne_extra.json",
    "cayenne_stores.json": GENERATED_DIR / "cayenne_stores.json",
    "excel_overlap_titles.json": GENERATED_DIR / "excel_overlap_titles.json",

    # Logo metadata
    "venue_logos.json": LOGO_DATA_DIR / "venue_logos.json",
    "logo_map.json": LOGO_DATA_DIR / "logo_map.json",
    "fb_logos.json": LOGO_DATA_DIR / "fb_logos.json",
    "fb_pages.json": LOGO_DATA_DIR / "fb_pages.json",
    "artemperor_logos.json": LOGO_DATA_DIR / "artemperor_logos.json",

    # Reference data
    "town_centroids.json": REFERENCE_DIR / "town_centroids.json",

    # Caches
    "enrich_cache_v3.json": CACHE_DIR / "enrich_cache_v3.json",
    "imgcache_v3.json": CACHE_DIR / "imgcache_v3.json",
    "event_kv_cache.json": CACHE_DIR / "event_kv_cache.json",
    "geocode_cache.json": CACHE_DIR / "geocode_cache.json",
    "arcgis_geocode_cache.json": CACHE_DIR / "arcgis_geocode_cache.json",
    "_short_url_resolved.json": CACHE_DIR / "_short_url_resolved.json",

    # Reports and working audit artifacts
    "_report_prev.json": REPORTS_DIR / "_report_prev.json",
    "_approx_location_report.json": REPORTS_DIR / "_approx_location_report.json",
    "_missing_logo_report.json": REPORTS_DIR / "_missing_logo_report.json",
    "_missing_logo_reason_report.json": REPORTS_DIR / "_missing_logo_reason_report.json",
    "_missing_logo_reason_report.md": REPORTS_DIR / "_missing_logo_reason_report.md",
    "_missing_event_links.json": REPORTS_DIR / "_missing_event_links.json",
    "_missing_event_kv.json": REPORTS_DIR / "_missing_event_kv.json",
    "_social_scan.json": REPORTS_DIR / "_social_scan.json",
    "_logo_source_candidates.json": REPORTS_DIR / "_logo_source_candidates.json",
    "_resolved_logo_candidates.json": REPORTS_DIR / "_resolved_logo_candidates.json",
    "_分類對照_20260627.csv": REPORTS_DIR / "_分類對照_20260627.csv",
    "_excel_backups": ARCHIVE_DIR / "backups" / "excel",
    "_logo_debug": RUNTIME_DIR / "debug" / "logo",
    "profiles": RUNTIME_DIR / "profiles" / "browser",
}


def path(name: str, *parts: str) -> str:
    """Return the canonical path for a legacy project filename."""
    if name.startswith("logos/"):
        return str(PUBLIC_DIR.joinpath(name, *parts))
    base = _FILES.get(name)
    if base is None:
        backend_candidate = BACKEND_DIR / name
        base = backend_candidate if backend_candidate.exists() else ROOT / name
    return str(base.joinpath(*parts))


def root_path(*parts: str) -> str:
    return str(ROOT.joinpath(*parts))


def runtime_path(*parts: str) -> str:
    return str(RUNTIME_DIR.joinpath(*parts))


def ensure_layout() -> None:
    for folder in (
        PUBLIC_DIR, MANUAL_DIR, GENERATED_DIR, CACHE_DIR, LOGO_DATA_DIR,
        REFERENCE_DIR, REPORTS_DIR, DOCS_DIR, OPS_DIR, ARCHIVE_DIR,
        RUNTIME_DIR, RUNTIME_DIR / "debug", RUNTIME_DIR / "profiles",
        RUNTIME_DIR / "cache",
    ):
        folder.mkdir(parents=True, exist_ok=True)


ensure_layout()
