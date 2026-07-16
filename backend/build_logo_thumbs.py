#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Build small local thumbnails for map marker logos."""
import json
from paths import path as P
import os
import tempfile
from pathlib import Path

from PIL import Image, ImageOps, ImageSequence

HERE = Path(__file__).resolve().parent
LOGODIR = Path(P("logos"))
THUMBDIR = LOGODIR / "_thumbs"
SIZE = 96
QUALITY = 78
WEBP_METHOD = 3


def logo_paths():
    paths = set()
    venues_path = Path(P("venues.json"))
    if venues_path.exists():
        data = json.load(open(venues_path, encoding="utf-8"))
        for venue in data.get("venues", []):
            logo = str(venue.get("logo") or "")
            if logo.startswith("logos/"):
                paths.add(Path(P(logo)))
    return sorted(p for p in paths if p.exists() and p.is_file())


def thumb_path(src):
    rel = src.relative_to(LOGODIR)
    stem = rel.with_suffix("")
    ext = src.suffix.lower().lstrip(".") or "img"
    return THUMBDIR / stem.parent / f"{stem.name}_{ext}.webp"


def prune_stale_thumbs(logos):
    """Remove generated thumbnails that are no longer used by venues.json."""
    expected = {thumb_path(src).resolve() for src in logos}
    removed = 0
    if THUMBDIR.exists():
        for candidate in THUMBDIR.rglob("*.webp"):
            if candidate.resolve() not in expected:
                candidate.unlink()
                removed += 1
        for folder in sorted(
            (p for p in THUMBDIR.rglob("*") if p.is_dir()),
            key=lambda p: len(p.parts),
            reverse=True,
        ):
            try:
                folder.rmdir()
            except OSError:
                pass
    return removed


def fit_canvas(img):
    img = ImageOps.exif_transpose(img)
    if img.mode not in ("RGBA", "LA"):
        img = img.convert("RGBA")
    else:
        img = img.convert("RGBA")
    img.thumbnail((SIZE, SIZE), Image.Resampling.LANCZOS)
    canvas = Image.new("RGBA", (SIZE, SIZE), (255, 255, 255, 0))
    canvas.alpha_composite(img, ((SIZE - img.width) // 2, (SIZE - img.height) // 2))
    return canvas


def raster_thumb(src, dst):
    with Image.open(src) as img:
        frames = []
        try:
            for frame in ImageSequence.Iterator(img):
                frames.append(frame.copy())
        except Exception:
            frames = [img.copy()]
        frame = max(frames, key=lambda im: im.width * im.height) if frames else img.copy()
        out = fit_canvas(frame)
        dst.parent.mkdir(parents=True, exist_ok=True)
        out.save(dst, "WEBP", quality=QUALITY, method=WEBP_METHOD)


def svg_thumb(page, src, dst):
    uri = src.as_uri()
    html = f"""<!doctype html>
<meta charset="utf-8">
<style>
html,body{{margin:0;width:{SIZE}px;height:{SIZE}px;background:transparent}}
.box{{width:{SIZE}px;height:{SIZE}px;display:flex;align-items:center;justify-content:center;background:transparent}}
img{{display:block;max-width:{SIZE}px;max-height:{SIZE}px;object-fit:contain}}
</style>
<div class="box"><img src="{uri}"></div>
"""
    page.set_content(html, wait_until="load")
    page.locator(".box").screenshot(path=str(dst), omit_background=True)


def main():
    logos = logo_paths()
    removed = prune_stale_thumbs(logos)
    raster = [p for p in logos if p.suffix.lower() != ".svg"]
    svgs = [p for p in logos if p.suffix.lower() == ".svg"]
    made = skipped = failed = 0

    for src in raster:
        dst = thumb_path(src)
        try:
            if dst.exists() and dst.stat().st_mtime >= src.stat().st_mtime:
                skipped += 1
                continue
            raster_thumb(src, dst)
            made += 1
        except Exception as exc:
            failed += 1
            print(f"FAIL raster {src.relative_to(LOGODIR.parent)}: {type(exc).__name__}: {exc}")

    pending_svgs = []
    for src in svgs:
        dst = thumb_path(src)
        if dst.exists() and dst.stat().st_mtime >= src.stat().st_mtime:
            skipped += 1
        else:
            pending_svgs.append(src)

    if pending_svgs:
        try:
            from playwright.sync_api import sync_playwright

            with sync_playwright() as p:
                browser = p.chromium.launch()
                page = browser.new_page(viewport={"width": SIZE, "height": SIZE}, device_scale_factor=1)
                for src in pending_svgs:
                    dst = thumb_path(src)
                    try:
                        dst.parent.mkdir(parents=True, exist_ok=True)
                        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
                            tmp_path = Path(tmp.name)
                        try:
                            svg_thumb(page, src, tmp_path)
                            with Image.open(tmp_path) as img:
                                fit_canvas(img).save(dst, "WEBP", quality=QUALITY, method=WEBP_METHOD)
                        finally:
                            try:
                                tmp_path.unlink()
                            except FileNotFoundError:
                                pass
                        made += 1
                    except Exception as exc:
                        failed += 1
                        print(f"FAIL svg {src.relative_to(LOGODIR.parent)}: {type(exc).__name__}: {exc}")
                browser.close()
        except Exception as exc:
            failed += len(pending_svgs)
            print(f"FAIL svg renderer: {type(exc).__name__}: {exc}")

    print(json.dumps({
        "logos": len(logos),
        "made": made,
        "skipped": skipped,
        "failed": failed,
        "removed_stale": removed,
    }, ensure_ascii=False))


if __name__ == "__main__":
    main()
