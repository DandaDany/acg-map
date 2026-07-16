#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Open the dedicated Facebook logo crawler browser profile.

Run this once when Facebook login is needed:
  python3 open_fb_logo_profile.py

Log in to Facebook in the browser window, then press Enter in the terminal to
close it. The session is saved in profiles/fb_logo_chrome and reused by
collect_fb_logos.py.
"""
import os
from paths import path as P
import time

from playwright.sync_api import sync_playwright


HERE = os.path.dirname(os.path.abspath(__file__))
PROFILE_DIR = os.environ.get(
    "FB_LOGO_PROFILE_DIR",
    P("profiles", "fb_logo_chrome"),
)


def main():
    os.makedirs(PROFILE_DIR, exist_ok=True)
    minutes = int(os.environ.get("FB_LOGIN_WAIT_MINUTES", "15"))
    with sync_playwright() as p:
        ctx = p.chromium.launch_persistent_context(
            PROFILE_DIR,
            headless=False,
            ignore_https_errors=True,
            viewport={"width": 1366, "height": 900},
            user_agent=(
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124 Safari/537.36"
            ),
        )
        page = ctx.pages[0] if ctx.pages else ctx.new_page()
        page.goto("https://www.facebook.com/", wait_until="domcontentloaded", timeout=30000)
        print("Facebook login browser opened.")
        print(f"Profile dir: {PROFILE_DIR}")
        print(f"Keeping browser open for {minutes} minutes. Log in, then tell Codex when finished.")
        deadline = time.time() + minutes * 60
        try:
            while time.time() < deadline:
                time.sleep(1)
        except KeyboardInterrupt:
            pass
        try:
            ctx.close()
        except Exception:
            pass


if __name__ == "__main__":
    main()
