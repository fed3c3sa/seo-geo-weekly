#!/usr/bin/env python3
"""Ping IndexNow (Bing, Yandex, Seznam, Naver...; Bing feeds Copilot and ChatGPT search) for changed URLs.
Works on macOS, Linux and Windows (uses curl, preinstalled on all three).

Usage:  indexnow.py <origin> <key> /path/ [/other/ ...]
   e.g. indexnow.py https://www.example.com 0123abcd... / /blog/post/ /sitemap.xml

The key file <origin>/<key>.txt must be live and contain exactly the key.
200 or 202 = accepted. 403 = key file missing or wrong. 422 = URL not on that host. 429 = too many requests.
"""
import subprocess
import sys
from urllib.parse import quote

if len(sys.argv) < 4:
    sys.exit(__doc__)
origin, key, paths = sys.argv[1].rstrip("/"), sys.argv[2], sys.argv[3:]


def curl(*args):
    return subprocess.run(["curl", "-s", "--max-time", "20", *args], capture_output=True, text=True).stdout


got = curl(f"{origin}/{key}.txt").strip()
if got != key:
    sys.exit(f"key file {origin}/{key}.txt is not live or holds something else (got: {got[:40]!r})")
for p in paths:
    url = origin + (p if p.startswith("/") else "/" + p)
    code = curl("-o", "/dev/null" if sys.platform != "win32" else "NUL", "-w", "%{http_code}",
                f"https://api.indexnow.org/indexnow?url={quote(url, safe='')}&key={key}")
    print(code, p)
