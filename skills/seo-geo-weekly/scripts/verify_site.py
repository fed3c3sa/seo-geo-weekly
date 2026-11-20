#!/usr/bin/env python3
"""Pre-push SEO gates for a site you have as files (a static site, or a generator's build output).

Usage:
  verify_site.py <site_root> --site https://www.example.com [options]

Options:
  --site URL          the canonical origin (resolves og:image, @id and sitemap URLs)
  --title-max N       hard limit for <title> (default 65)
  --desc-max N        hard limit for the meta description (default 160)
  --no-dashes         fail on em or en dashes (a house rule some owners have)
  --require TEXT      every indexable page must contain TEXT (repeatable, e.g. a co-author's name)
  --exclude DIR       skip a sub-folder (repeatable; node_modules and .git are always skipped)

Exit code 1 if any hard gate fails. One line per page, then site-wide checks.
For a live site you can't edit as files (WordPress, Shopify, Wix...), use audit_live.py instead.
"""
import argparse
import glob
import os
import re
import sys
import xml.dom.minidom
from urllib.parse import urlparse

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from seo_checks import attr_value, blocks_all, canonical, check_page, line, meta, robots_groups  # noqa: E402

ap = argparse.ArgumentParser()
ap.add_argument("root")
ap.add_argument("--site", required=True)
ap.add_argument("--title-max", type=int, default=65)
ap.add_argument("--desc-max", type=int, default=160)
ap.add_argument("--no-dashes", action="store_true")
ap.add_argument("--require", action="append", default=[])
ap.add_argument("--exclude", action="append", default=[])
a = ap.parse_args()
root, SITE = a.root, a.site.rstrip("/")
skip = {"node_modules", ".git"} | set(a.exclude)


def local_path(url_path, page_dir):
    """Map an href/src to a file in the site folder, or None if it does not exist."""
    base = os.path.join(root, url_path.lstrip("/")) if url_path.startswith("/") else os.path.normpath(os.path.join(page_dir, url_path))
    for cand in (base, os.path.join(base, "index.html"), base + ".html"):
        if os.path.isfile(cand):
            return cand
    return None


pages = [p for p in glob.glob(os.path.join(root, "**", "*.html"), recursive=True)
         if not set(os.path.relpath(p, root).split(os.sep)) & skip]

fail = 0
canon_of = {}
for p in sorted(pages):
    t = open(p, encoding="utf-8", errors="replace").read()
    rel = os.path.relpath(p, root)
    robots = (meta(t, "name", "robots") or "").lower()
    refresh = re.search(r'http-equiv="refresh"', t, re.I)
    if re.match(r"google[0-9a-f]+\.html$", os.path.basename(p)) or (refresh and "noindex" in robots):
        print(f"--  {rel:45} skipped (verification file or noindex redirect)")
        continue
    indexable = "noindex" not in robots and os.path.basename(p) != "404.html"
    issues, notes, info = check_page(t, site=SITE, indexable=indexable, title_max=a.title_max,
                                     desc_max=a.desc_max, no_dashes=a.no_dashes, require=a.require)
    for k in ("og:image", "twitter:image"):
        img = meta(t, "property", k) or meta(t, "name", k)
        if img and img.startswith(SITE) and not local_path(urlparse(img).path, os.path.dirname(p)):
            issues.append(f"{k} file missing {urlparse(img).path}")
    for tag in re.findall(r"<(?:a|link|img|script|source)\b[^>]*>", t, re.I):
        for at in ("href", "src"):
            ref = attr_value(tag, at)
            if not ref:
                continue
            for origin in (SITE, SITE.replace("https://", "http://"), "//" + urlparse(SITE).netloc):
                if ref.startswith(origin + "/") or ref == origin:
                    ref = ref[len(origin):] or "/"
            if re.match(r"^[a-z][a-z0-9+.-]*:|^//|^#", ref, re.I):
                continue  # external, mailto:, tel:, data:, javascript:, in-page anchor
            ref = re.split(r"[#?]", ref)[0]
            if ref and not local_path(ref, os.path.dirname(p)):
                issues.append(f"broken link {ref[:50]}")
    if indexable:
        canon_of[rel] = canonical(t)
    if t.count("<div") != t.count("</div>"):
        issues.append(f'div balance {t.count("<div") - t.count("</div>")}')
    fail |= bool(issues)
    print(line("OK " if not issues else "ERR", rel, info, issues, notes))

sm_path = os.path.join(root, "sitemap.xml")
if os.path.exists(sm_path):
    try:
        sm = xml.dom.minidom.parse(sm_path)
        locs = [n.firstChild.data.strip() for n in sm.getElementsByTagName("loc")]
        page_locs = [u for u in locs if u.startswith(SITE) and not re.search(r"\.(png|jpe?g|webp|gif|pdf|mp4|webm|xml)$", u, re.I)]
        missing = [u for u in page_locs if not local_path(urlparse(u).path or "/", root)]
        foreign = [u for u in locs if not u.startswith(SITE)]
        mismatch = []
        for u in page_locs:
            f = local_path(urlparse(u).path or "/", root)
            c = canon_of.get(os.path.relpath(f, root)) if f else None
            if c and c.rstrip("/") != u.rstrip("/"):
                mismatch.append(f"{urlparse(u).path} -> canonical {c}")
            elif f and os.path.relpath(f, root) not in canon_of:
                mismatch.append(f"{urlparse(u).path} is noindex or skipped")
        for m in mismatch:
            print(f"ERR sitemap lists a non-canonical URL: {m}")
        fail |= bool(mismatch)
        print(f"{'OK ' if not missing else 'ERR'} sitemap.xml {len(locs)} <loc>"
              + (f"  no file for {missing}" if missing else "")
              + (f"  (note: {len(foreign)} URLs not on {SITE}: www/http mismatch?)" if foreign else ""))
        fail |= bool(missing)
    except Exception as e:  # noqa: BLE001
        print(f"ERR sitemap.xml does not parse: {e}")
        fail = 1
else:
    print("WARN no sitemap.xml")
rb = os.path.join(root, "robots.txt")
if os.path.exists(rb):
    rt = open(rb, encoding="utf-8").read()
    has_sm = re.search(r"(?im)^\s*sitemap:", rt)
    print(("OK " if has_sm else "WARN") + " robots.txt" + ("" if has_sm else " has no Sitemap: line"))
    if blocks_all(robots_groups(rt)):
        print("ERR robots.txt disallows the whole site (User-agent: * / Disallow: /)")
        fail = 1
else:
    print("WARN no robots.txt")
fp = os.path.join(root, "llms.txt")
if not os.path.exists(fp):
    print("WARN no llms.txt (optional, helps AI assistants)")
elif a.no_dashes:
    tx = open(fp, encoding="utf-8").read()
    bad = tx.count("—") + tx.count("–")
    print(f"{'OK ' if not bad else 'ERR'} llms.txt" + (f" dashes {bad}" if bad else ""))
    fail |= bool(bad)
sys.exit(fail)
