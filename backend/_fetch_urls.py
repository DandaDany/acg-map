#!/usr/bin/env python3
import sys
from paths import path as P
import urllib.request


def main():
    for url in sys.argv[1:]:
        print("---", url)
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=25) as r:
                data = r.read(8000).decode("utf-8", "ignore")
            print(data)
        except Exception as e:
            print(type(e).__name__, str(e)[:300])


if __name__ == "__main__":
    main()
