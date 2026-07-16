#!/usr/bin/env python3
import asyncio
from paths import path as P
import re
import sys
import urllib.parse

from playwright.async_api import async_playwright


async def lookup(page, query):
    url = "https://www.google.com/maps/search/" + urllib.parse.quote(query)
    await page.goto(url, wait_until="domcontentloaded", timeout=60000)
    await page.wait_for_timeout(5000)
    current = page.url
    text = ""
    try:
        text = await page.locator("body").inner_text(timeout=5000)
    except Exception:
        pass
    coords = []
    for haystack in (current, text):
        coords.extend(re.findall(r"@(-?\d+\.\d+),(-?\d+\.\d+)", haystack))
        coords.extend(re.findall(r"!3d(-?\d+\.\d+)!4d(-?\d+\.\d+)", haystack))
    return current, coords[:5], text[:1000]


async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page(
            user_agent=(
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125 Safari/537.36"
            )
        )
        for query in sys.argv[1:]:
            print("---", query)
            try:
                url, coords, text = await lookup(page, query)
                print(url)
                print(coords)
                print(text)
            except Exception as e:
                print("ERR", type(e).__name__, str(e)[:300])
        await browser.close()


if __name__ == "__main__":
    asyncio.run(main())
