#!/usr/bin/env python3
import asyncio
from paths import path as P
import json
import re
import sys
from urllib.parse import urljoin

from playwright.async_api import async_playwright

BASE = "https://artemperor.tw"


def norm(s):
    return re.sub(r"\s+", "", (s or "").replace("臺", "台").lower())


def similar(a, b):
    if len(a) < 2 or len(b) < 2:
        return False
    return a in b or b in a


async def main():
    targets = sys.argv[1:]
    target_norms = {norm(t): t for t in targets}
    matches = {}
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page(
            user_agent=(
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/125.0.0.0 Safari/537.36"
            )
        )
        for page_no in range(1, 9):
            url = f"{BASE}/museums?page={page_no}"
            await page.goto(url, wait_until="domcontentloaded", timeout=45000)
            await page.wait_for_timeout(1000)
            links = await page.locator("a").evaluate_all(
                """els => els.map(a => ({text:a.innerText || a.textContent || '', href:a.href})).filter(x => x.href)"""
            )
            for link in links:
                text = link["text"].strip()
                href = link["href"]
                if not text or href.endswith("#") or "/museums/" not in href:
                    continue
                ntext = norm(text)
                for nt, original in target_norms.items():
                    if similar(nt, ntext) and original not in matches:
                        detail = await browser.new_page()
                        try:
                            await detail.goto(urljoin(BASE, href), wait_until="domcontentloaded", timeout=45000)
                            await detail.wait_for_timeout(1000)
                            body = await detail.locator("body").inner_text(timeout=10000)
                            matches[original] = {"list_text": text, "url": href, "body": body[:5000]}
                            print("MATCH", original, href, flush=True)
                        except Exception as e:
                            matches[original] = {"list_text": text, "url": href, "error": str(e)[:300]}
                        finally:
                            await detail.close()
            print("PAGE", page_no, "done", flush=True)
        await browser.close()
    print(json.dumps(matches, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    asyncio.run(main())
