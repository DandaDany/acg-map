#!/usr/bin/env python3
import asyncio
from paths import path as P
import sys

from playwright.async_api import async_playwright


async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        for url in sys.argv[1:]:
            print("---", url)
            page = await browser.new_page()
            try:
                await page.goto(url, wait_until="domcontentloaded", timeout=45000)
                await page.wait_for_timeout(1000)
                links = await page.locator("a").evaluate_all(
                    """els => els.map(a => ({text: (a.innerText || a.textContent || '').trim(), href: a.href})).filter(x => x.text || x.href)"""
                )
                for link in links:
                    print(link["text"], "|", link["href"])
            except Exception as e:
                print("ERR", type(e).__name__, str(e)[:300])
            finally:
                await page.close()
        await browser.close()


if __name__ == "__main__":
    asyncio.run(main())
