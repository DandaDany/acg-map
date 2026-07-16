#!/usr/bin/env python3
import asyncio
from paths import path as P
import sys
import urllib.parse

from playwright.async_api import async_playwright


async def scrape_google(page, query):
    url = "https://www.google.com/search?hl=zh-TW&q=" + urllib.parse.quote(query)
    await page.goto(url, wait_until="domcontentloaded", timeout=45000)
    await page.wait_for_timeout(2000)
    return await page.locator("body").inner_text(timeout=10000)


async def scrape_bing(page, query):
    url = "https://www.bing.com/search?setlang=zh-TW&q=" + urllib.parse.quote(query)
    await page.goto(url, wait_until="domcontentloaded", timeout=45000)
    await page.wait_for_timeout(2000)
    return await page.locator("body").inner_text(timeout=10000)


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
            for label, fn in (("google", scrape_google), ("bing", scrape_bing)):
                try:
                    text = await fn(page, query)
                    if "系統偵測到您的電腦網路送出的流量有異常" in text:
                        print("ERR", label, "captcha")
                        continue
                    print("###", label)
                    print(text[:4000])
                    break
                except Exception as e:
                    print("ERR", label, type(e).__name__, str(e)[:200])
        await browser.close()


if __name__ == "__main__":
    asyncio.run(main())
