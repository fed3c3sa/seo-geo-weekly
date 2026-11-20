# Changelog

## 1.0.0 (2026-11-20)

First public release.

- `SKILL.md`: the weekly SEO / GEO / AEO loop: setup check, data, diagnosis rules, safe editing, gates, independent review, publishing, indexing requests, report, off-site checklist.
- Guided first-time setup (`references/setup.md`): Claude in Chrome, Google sign-in, Search Console (Domain or URL-prefix; DNS hosts and CMS platforms), Bing Webmaster Tools, IndexNow, the files every site needs, and a manual route without the browser extension.
- `references/consoles.md`: reading Search Console, Bing Webmaster and clean search results through Chrome.
- `references/scheduling.md` + `scripts/schedule.py`: a weekly run on your own computer (launchd, cron or Task Scheduler) that opens a visible Claude Code session with Chrome. The scheduler runs a stable copy in `~/.seo-geo-weekly/`, so plugin updates don't break it.
- Scripts (Python 3 + curl, no other dependencies): `audit_live.py` (read-only technical and on-page audit of any live site), `verify_site.py` (pre-publish gates for a folder of HTML), `compare.py` (run-over-run numbers), `indexnow.py`.
- Tests and CI on Linux, macOS and Windows.
