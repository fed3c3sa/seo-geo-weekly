#!/usr/bin/env python3
"""Technical baseline + on-page audit of a LIVE site, any platform (static, WordPress, Shopify, Wix, Webflow...).
Read-only: it only sends GET requests. Uses curl (installed on macOS, Linux and Windows 10+).

Usage:
  audit_live.py https://www.example.com [--sitemap URL] [--max 40] [--no-dashes] [--require TEXT] [--only-baseline]

It prints:
  1. Baseline: every http/https/www/apex variant should 301 once to the canonical origin; a missing page must be a
     real 404; robots.txt, sitemap(s), llms.txt; noindex headers; which DNS/CDN serves the site.
  2. One line per page from the sitemap (up to --max): status, redirects, self-canonical, noindex,
     title/description length, h1, lang, alt text, JSON-LD types, FAQ sync.
Exit code 1 if a hard problem is found.
"""
import argparse
import os
import re
import subprocess
import sys
import tempfile
import xml.dom.minidom
from urllib.parse import urlparse

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from seo_checks import blocks_all, canonical, check_page, line, meta, robots_groups  # noqa: E402

UA = "Mozilla/5.0 (compatible; seo-geo-audit/1.0)"
ap = argparse.ArgumentParser()
ap.add_argument("origin")
ap.add_argument("--sitemap")
ap.add_argument("--max", type=int, default=40)
ap.add_argument("--title-max", type=int, default=65)
ap.add_argument("--desc-max", type=int, default=160)
ap.add_argument("--no-dashes", action="store_true")
ap.add_argument("--require", action="append", default=[])
ap.add_argument("--only-baseline", action="store_true")
a = ap.parse_args()
O = a.origin.rstrip("/")
host = urlparse(O).hostname or ""
apex = host[4:] if host.startswith("www.") else host
fail = 0


def get(url, follow=False, body=True):
    """Return (status, final_url, location, headers_lowercase_dict, body_text)."""
    with tempfile.TemporaryDirectory() as d:
        hf, bf = os.path.join(d, "h"), os.path.join(d, "b")
        cmd = ["curl", "-s", "--max-time", "25", "-A", UA, "-D", hf, "-o", bf if body else os.devnull,
               "-w", "%{http_code} %{url_effective} %{redirect_url}"]
        if follow:
            cmd += ["-L", "--max-redirs", "6"]
        try:
            out = subprocess.run(cmd + [url], capture_output=True, text=True, timeout=40).stdout.split(" ")
        except Exception:  # noqa: BLE001
            return 0, url, "", {}, ""
        code = int(out[0]) if out and out[0].isdigit() else 0
        final, loc = (out + ["", "", ""])[1:3]
        headers = {}
        if os.path.exists(hf):
            for ln in open(hf, encoding="latin-1"):
                if ":" in ln:
                    k, v = ln.split(":", 1)
                    headers[k.strip().lower()] = v.strip()  # last response wins when following
        text = open(bf, encoding="utf-8", errors="replace").read() if body and os.path.exists(bf) else ""
        return code, final, loc, headers, text


def say(status, msg):
    global fail
    if status == "ERR":
        fail = 1
    print(f"{status:4} {msg}")


print(f"# Baseline for {O}\n")
variants = sorted({f"{s}://{h}/" for s in ("http", "https") for h in (apex, "www." + apex)})
for v in variants:
    code, _, loc, _, _ = get(v, body=False)
    if v == O + "/":
        say("OK " if code == 200 else "ERR", f"{v:40} {code} (the canonical origin itself)")
        continue
    if code == 0:
        say("NOTE", f"{v:40} no answer (fine if that host is not used at all)")
        continue
    hops, url, codes = 0, v, []
    while code in (301, 302, 303, 307, 308) and hops < 6:
        codes.append(code)
        url = loc
        code, _, loc, _, _ = get(url, body=False)
        hops += 1
    chain = "->".join(map(str, codes + [code]))
    ok = url.rstrip("/") == O and codes and codes[0] in (301, 308)
    if ok and hops == 1:
        say("OK ", f"{v:40} {chain} -> {url}")
    elif ok:
        say("WARN", f"{v:40} {chain} -> {url}  ({hops} hops; one 301 is better)")
    elif not codes and code == 200:
        say("ERR", f"{v:40} 200: a duplicate copy of the site is live (should 301 to {O}/)")
    else:
        say("WARN", f"{v:40} {chain} -> {url or '?'}  (expected one 301 to {O}/)")

code, _, _, _, _ = get(O + "/this-page-should-not-exist-" + "x7q", body=False)
say("OK " if code == 404 else ("WARN" if code == 410 else "ERR"),
    f"missing page answers {code} (want 404; 200 = soft 404)")

code, final, _, h, home = get(O + "/", follow=True)
xr = h.get("x-robots-tag", "")
say("ERR" if "noindex" in xr.lower() else "OK ", f"home {code}, X-Robots-Tag: {xr or 'none'}")
say("NOTE", "served by: " + ", ".join(f"{k}={h[k]}" for k in ("server", "cf-cache-status", "x-powered-by", "via", "x-vercel-id", "x-nf-request-id") if k in h))
hrob = (meta(home, "name", "robots") or "").lower()
if "noindex" in hrob:
    say("ERR", f"home has <meta name=robots content={hrob!r}>")
can = canonical(home)
say("OK " if can and can.rstrip("/") == O else "WARN", f"home canonical: {can}")
for name in ("google-site-verification", "msvalidate.01"):
    v = meta(home, "name", name)
    say("NOTE", f"{name} meta tag: {'present' if v else 'absent (fine if verified another way)'}")

code, _, _, _, robots = get(O + "/robots.txt", follow=True)
sitemaps = re.findall(r"(?im)^\s*sitemap:\s*(\S+)", robots) if code == 200 else []
if code != 200:
    say("WARN", f"robots.txt answers {code}")
else:
    groups = robots_groups(robots)
    say("WARN" if blocks_all(groups) else "OK ", f"robots.txt {len(robots)} bytes, Sitemap lines: {len(sitemaps)}"
        + ("  (the * group blocks the whole site for every crawler without its own group)" if blocks_all(groups) else ""))
    search_bots = ("Googlebot", "Bingbot")
    ai_search = ("OAI-SearchBot", "ChatGPT-User", "Claude-SearchBot", "Claude-User", "PerplexityBot", "Perplexity-User")
    training = ("GPTBot", "ClaudeBot", "Google-Extended", "Applebot-Extended", "CCBot")
    for bot in search_bots + ai_search + training:
        if not blocks_all(groups, bot):
            continue
        if bot in search_bots:
            say("ERR", f"robots.txt blocks {bot}: the site cannot rank on {'Google' if bot == 'Googlebot' else 'Bing, Copilot or ChatGPT search'}")
        elif bot in ai_search:
            say("WARN", f"robots.txt blocks {bot}: keeps the site out of that assistant's search answers (fine only if the owner wants that)")
        elif bot == "Google-Extended":
            say("NOTE", "robots.txt blocks Google-Extended: no Gemini training or Gemini/Vertex grounding; Google Search and AI Overviews are unaffected")
        else:
            say("NOTE", f"robots.txt blocks {bot}: a training crawler, the owner's choice; search rankings are unaffected")

sm_url = a.sitemap or (sitemaps[0] if sitemaps else O + "/sitemap.xml")
urls, seen = [], set()


def read_sitemap(u, depth=0):
    if u in seen or depth > 2:
        return
    seen.add(u)
    c, _, _, _, x = get(u, follow=True)
    if c != 200:
        say("ERR", f"sitemap {u} answers {c}")
        return
    try:
        dom = xml.dom.minidom.parseString(x.encode("utf-8"))
    except Exception as e:  # noqa: BLE001
        say("ERR", f"sitemap {u} does not parse: {e}")
        return
    if dom.getElementsByTagName("sitemapindex"):
        for n in dom.getElementsByTagName("loc"):
            read_sitemap(n.firstChild.data.strip(), depth + 1)
    else:
        locs = []
        for url_node in dom.getElementsByTagName("url"):
            loc = url_node.getElementsByTagName("loc")
            if loc and loc[0].firstChild:
                locs.append(loc[0].firstChild.data.strip())
        lm = len(dom.getElementsByTagName("lastmod"))
        say("OK ", f"sitemap {u}: {len(locs)} URLs, {lm} with <lastmod>")
        urls.extend(locs)


read_sitemap(sm_url)
if not urls:
    say("WARN", "no URLs from a sitemap: auditing the home page only")
    urls = [O + "/"]
foreign = [u for u in urls if not u.startswith(O + "/") and u != O]
if foreign:
    say("ERR", f"{len(foreign)} sitemap URLs are not on {O} (e.g. {foreign[0]}): list canonical URLs only")
code, _, _, _, llms = get(O + "/llms.txt", follow=True)
say("OK " if code == 200 and llms.strip() else "NOTE", f"llms.txt answers {code}" + ("" if code == 200 else " (optional, helps AI assistants)"))

if a.only_baseline:
    sys.exit(fail)

print(f"\n# Pages ({min(len(urls), a.max)} of {len(urls)} in the sitemap)\n")
for u in urls[: a.max]:
    code, final, _, h, t = get(u, follow=True)
    path = urlparse(u).path or "/"
    if code != 200:
        say("ERR", f"{path:45} answers {code}")
        continue
    issues = []
    if final.rstrip("/") != u.rstrip("/"):
        issues.append(f"redirects to {final} (the sitemap should list the final URL)")
    robots = ((meta(t, "name", "robots") or "") + " " + h.get("x-robots-tag", "")).lower()
    if "noindex" in robots:
        issues.append("noindex but listed in the sitemap")
    c = canonical(t)
    if c and c.rstrip("/") != u.rstrip("/"):
        issues.append(f"canonical points elsewhere: {c}")
    more, notes, info = check_page(t, site=O, indexable="noindex" not in robots, title_max=a.title_max,
                                   desc_max=a.desc_max, no_dashes=a.no_dashes, require=a.require)
    issues += more
    if info.get("types"):
        notes.append("schema " + "/".join(info["types"])[:80])
    print(line("OK " if not issues else "ERR", path[:45], info, issues, notes))
    if issues:
        fail = 1
sys.exit(fail)
