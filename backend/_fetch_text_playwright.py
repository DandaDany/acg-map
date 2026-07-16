#!/usr/bin/env python3
import asyncio
from paths import path as P
import sys

from playwright.async_api import async_playwright


async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page(
            user_agent=(
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/125.0.0.0 Safari/537.36"
            )
        )
        for url in sys.argv[1:]:
            print("---", url)
            try:
                await page.goto(url, wait_until="domcontentloaded", timeout=45000)
                await page.wait_for_timeout(1500)
                text = await page.locator("body").inner_text(timeout=10000)
                print(text[:20000])
            except Exception as e:
                print("ERR", type(e).__name__, str(e)[:300])
        await browser.close()


if __name__ == "__main__":
    asyncio.run(main())
