"""Shared on-page SEO checks, used by verify_site.py (local files) and audit_live.py (live URLs).

check_page(text, ...) returns (issues, notes, info):
  issues = hard problems (a gate fails), notes = soft warnings, info = short stats for the report line.
"""
import html
import json
import re


def clean(s):
    s = re.sub(r"</(?:li|p|h[1-6]|div)>|<br\s*/?>", " ", s)
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", "", s))).strip()


ATTR = r'\s*=\s*(?:"([^"]*)"|\'([^\']*)\'|([^\s"\'>]+))'


def attr_value(tag, name):
    """Value of attribute `name` in one tag, quoted with ", ' or not at all."""
    m = re.search(rf"\b{name}{ATTR}", tag, re.I)
    return html.unescape(next(g for g in m.groups() if g is not None)) if m else None


def meta(t, attr, name):
    """Value of <meta attr="name" content="...">, in either attribute order, any quoting."""
    for tag in re.findall(r"<meta\b[^>]*>", t, re.I):
        if (attr_value(tag, attr) or "").lower() == name.lower():
            c = attr_value(tag, "content")
            if c is not None:
                return c
    return None


def canonical(t):
    for tag in re.findall(r"<link\b[^>]*>", t, re.I):
        if "canonical" in (attr_value(tag, "rel") or "").lower().split():
            return attr_value(tag, "href") or ""
    return None


def jsonld_nodes(t):
    nodes, errors = [], []
    for b in re.findall(r'<script[^>]*type\s*=\s*["\']application/ld\+json["\'][^>]*>(.*?)</script>', t, re.S | re.I):
        try:
            d = json.loads(b)
            for x in (d if isinstance(d, list) else [d]):
                if isinstance(x, dict):
                    nodes += x.get("@graph", [x])
        except Exception as e:  # noqa: BLE001
            errors.append(f"JSON-LD does not parse ({str(e)[:60]})")
    return nodes, errors


def types_of(n):
    t = n.get("@type", []) if isinstance(n, dict) else []
    return t if isinstance(t, list) else [t]


def check_page(t, *, site, indexable=True, title_max=65, desc_max=160, no_dashes=False, require=()):
    issues, notes, info = [], [], {}
    title = re.search(r"<title[^>]*>(.*?)</title>", t, re.S | re.I)
    tl = len(html.unescape(clean(title.group(1)))) if title else 0
    desc = meta(t, "name", "description")
    dl = len(desc) if desc else 0
    info.update(title=tl, desc=dl)
    if not title or not tl:
        issues.append("no <title>")
    elif tl > title_max:
        issues.append(f"title {tl} chars > {title_max}")
    if len(re.findall(r"<title[\s>]", t, re.I)) > 1:
        issues.append("more than one <title>")
    if indexable:
        if not desc:
            issues.append("no meta description")
        elif dl > desc_max:
            issues.append(f"description {dl} chars > {desc_max}")
        if canonical(t) is None:
            issues.append("no canonical")
        h1 = len(re.findall(r"<h1[\s>]", t, re.I))
        if h1 != 1:
            issues.append(f"{h1} h1 tags (want 1)")
        if not re.search(r"<html[^>]*\blang\s*=", t, re.I):
            issues.append("no <html lang>")
        for k in ("og:title", "og:description", "og:image"):
            if not meta(t, "property", k):
                notes.append(f"no {k}")
        for r in re.findall(r"<img\b[^>]*>", t, re.I):
            if not re.search(r"\balt\s*=", r, re.I):
                src = re.search(r'src\s*=\s*["\']([^"\']+)', r, re.I)
                issues.append("img without alt: " + (src.group(1)[:40] if src else "?"))
        for req in require:
            if req not in t:
                issues.append(f"missing required text {req!r}")
    if no_dashes and (t.count("—") or t.count("–")):
        issues.append(f"dashes: em {t.count(chr(0x2014))}, en {t.count(chr(0x2013))}")

    nodes, errs = jsonld_nodes(t)
    issues += errs
    info["ld"] = len(nodes)
    info["types"] = sorted({ty for n in nodes for ty in types_of(n) if isinstance(ty, str)})
    ids, refs = set(), []

    def walk(x):
        if isinstance(x, dict):
            if list(x) == ["@id"]:
                refs.append(x["@id"])
            elif "@id" in x:
                ids.add(x["@id"])  # a definition, top-level or nested
            for v in x.values():
                walk(v)
        elif isinstance(x, list):
            for v in x:
                walk(v)

    walk(nodes)
    for r in sorted(set(refs)):
        if isinstance(r, str) and r.startswith(site) and r not in ids:
            issues.append(f"dangling @id {r.replace(site, '')}")

    faq = [n for n in nodes if isinstance(n, dict) and "FAQPage" in types_of(n)]
    if faq:
        ld = {}
        for q in faq[0].get("mainEntity", []) or []:
            try:
                ld[clean(q["name"])] = clean(q["acceptedAnswer"]["text"])
            except (KeyError, TypeError):
                issues.append("FAQPage entry without name/acceptedAnswer.text")
        vis = {}
        for d in re.findall(r"<details\b[^>]*>(.*?)</details>", t, re.S | re.I):
            q = re.search(r"<summary[^>]*>(.*?)</summary>", d, re.S | re.I)
            if q:
                vis[clean(q.group(1))] = clean(d[q.end():])
        if vis:  # only comparable when the FAQ is built from <details>
            ok = sum(1 for q, a in ld.items() if vis.get(q) == a)
            info["faq"] = f"{ok}/{len(ld)}"
            if ok != len(ld):
                issues.append("FAQ JSON-LD differs from the visible text: "
                              + ", ".join(q[:35] for q, a in ld.items() if vis.get(q) != a))
        else:
            notes.append("FAQPage present; visible FAQ not in <details>, compare it by hand")
    return issues, notes, info


def line(status, name, info, issues, notes):
    faq = f" FAQ {info['faq']}" if "faq" in info else ""
    s = f"{status} {name:45} title {info.get('title', 0)}c desc {info.get('desc', 0)}c ld {info.get('ld', 0)}{faq}"
    if issues:
        s += "  " + "; ".join(issues)
    if notes:
        s += "  (note: " + ", ".join(notes) + ")"
    return s


def robots_groups(text):
    """Parse robots.txt into {user-agent (lowercase): [disallow paths]} following the group rules."""
    groups, agents, in_rules = {}, [], False
    for raw in text.splitlines():
        ln = raw.split("#", 1)[0].strip()
        if ":" not in ln:
            continue
        k, v = (x.strip() for x in ln.split(":", 1))
        k = k.lower()
        if k == "user-agent":
            if in_rules:
                agents, in_rules = [], False
            agents.append(v.lower())
            groups.setdefault(v.lower(), [])
        elif k in ("disallow", "allow"):
            in_rules = True
            if k == "disallow":
                for ag in agents:
                    groups[ag].append(v)
    return groups


def blocks_all(groups, agent="*"):
    """True if `agent` may not crawl the site root. A bot with no group of its own follows the * group."""
    rules = groups.get(agent.lower())
    if rules is None:
        rules = groups.get("*", [])
    return any(r in ("/", "/*") for r in rules)
