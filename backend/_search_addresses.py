#!/usr/bin/env python3
import html
from paths import path as P
import re
import sys
import time
import urllib.parse
import urllib.request


def strip_tags(text):
    return html.unescape(re.sub(r"<.*?>", "", text)).strip()


def search(query):
    url = "https://duckduckgo.com/html/?q=" + urllib.parse.quote(query)
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=25) as r:
        data = r.read().decode("utf-8", "ignore")
    results = []
    links = re.finditer(
        r'<a rel="nofollow" class="result__a" href="([^"]+)"[^>]*>(.*?)</a>',
        data,
        re.S,
    )
    snippets = re.findall(r'<a class="result__snippet"[^>]*>(.*?)</a>', data, re.S)
    for i, m in enumerate(links):
        title = strip_tags(m.group(2))
        href = html.unescape(m.group(1))
        snippet = strip_tags(snippets[i]) if i < len(snippets) else ""
        results.append((title, href, snippet))
    return results


def main():
    for query in sys.argv[1:]:
        print("---", query)
        try:
            for title, href, snippet in search(query)[:8]:
                print(title)
                print(href)
                if snippet:
                    print("  ", snippet[:500])
        except Exception as e:
            print("ERR", type(e).__name__, e)
        time.sleep(0.5)


if __name__ == "__main__":
    main()
