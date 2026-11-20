# seo-geo-weekly

**A Claude Code skill that improves your website's visibility in Google and Bing (SEO) and in AI answers (GEO): Google AI Overviews, ChatGPT search, Microsoft Copilot, Perplexity.**

It works from your real data in Google Search Console and Bing Webmaster Tools, which Claude reads for you through the Claude in Chrome extension. It works on any site: a static site in a git repo, WordPress, Shopify, Wix, Webflow, Squarespace or Ghost.

Starting from zero? The skill first walks you through everything that's missing:
- installing and connecting Claude in Chrome;
- signing in;
- adding and verifying your site in Search Console and Bing;
- submitting the sitemap;
- setting up IndexNow.

Claude does every step it can. You click only where your identity is needed: sign-ins, consent screens, your DNS or site admin. It never asks for your passwords.

[![tests](https://github.com/fed3c3sa/seo-geo-weekly/actions/workflows/tests.yml/badge.svg)](https://github.com/fed3c3sa/seo-geo-weekly/actions/workflows/tests.yml)
![license](https://img.shields.io/badge/license-MIT-blue)

---

## Install

**Option A: as a Claude Code plugin** (recommended, easy to update). Inside Claude Code:

```
/plugin marketplace add fed3c3sa/seo-geo-weekly
/plugin install seo-geo-weekly@seo-geo-weekly
```

**Option B: with the skills CLI.**

```bash
npx skills add fed3c3sa/seo-geo-weekly@seo-geo-weekly -g -y
```

**Option C: by hand.** Download `seo-geo-weekly.zip` from the [latest release](https://github.com/fed3c3sa/seo-geo-weekly/releases/latest) and unzip it into your skills folder:

```bash
mkdir -p ~/.claude/skills && unzip seo-geo-weekly.zip -d ~/.claude/skills/
```

- **Windows:** the skills folder is `%USERPROFILE%\.claude\skills\`.
- **One project only:** use `<project>/.claude/skills/`.

Then restart Claude Code.

## Use

Start Claude Code with Chrome attached (`claude --chrome`, or `/chrome` inside a session) and ask in your own words:

- "Improve the SEO and GEO of https://www.mysite.com"
- "Set up Search Console and Bing for mysite.com"
- "Why doesn't my site show up when people search my name?"
- "Run this week's SEO pass"
- "Schedule the SEO run for mysite.com every Wednesday morning"

**The first time:** Claude checks what's already in place and guides you through the rest. Then it takes a technical baseline of the site.

**After that:** real Search Console numbers arrive 2 to 3 days after verification, so the first full data-driven run comes then. Run it weekly from there, or let the skill schedule itself.

## What happens each week

1. **Data:**
   - Search Console: 28-day totals, queries, pages, countries, daily rows, indexing;
   - Bing: search performance, plus **AI Performance**, the Copilot citations report;
   - clean, non-personalized search results for the queries that matter;
   - a technical audit of the live site.
2. **Diagnosis**, highest value first:
   - wrong facts;
   - indexing problems;
   - entity and brand signals;
   - questions that AI answers pick up;
   - near-duplicate queries;
   - titles and descriptions with poor click-through.
3. **A handful of true changes.** Every fact is checked against a primary source that day, and each change is recorded so next week can tell what worked.
4. **Gates:** automated checks of titles, descriptions, canonicals, structured data, FAQ sync, links, sitemap and robots.txt.
5. **An independent review** by a separate agent before anything is indexed.
6. **Publish**, but only what you authorized. Then request indexing on Google and Bing and ping IndexNow.
7. **A short report:** what moved, what changed and why, what to check next time, and the off-site steps only you can do (profile links, store listings).

## Run it every week on its own

At the end of setup, Claude offers to schedule the loop. Your computer's own scheduler opens a visible Claude Code session with Chrome every week:
- **macOS:** launchd;
- **Linux:** cron;
- **Windows:** Task Scheduler.

The session runs the loop and sends a desktop notification with the result.

```bash
S=<skill folder>/scripts/schedule.py      # after install, also ~/.seo-geo-weekly/schedule.py
python3 $S install mysite.com --day wed --time 10:07   # safe permissions by default
python3 $S run mysite.com --test                       # one-minute check, with you watching
python3 $S status                                      # or: remove mysite.com
```

You don't need to type these: Claude runs them for you during setup.

Why not Claude Code's other schedulers:
- **Cloud routines (`/schedule`):** they run on Anthropic's servers and can't reach your signed-in Chrome, so they can't read Search Console.
- **`/loop`:** it lives only while one session stays open.

Details are in [`references/scheduling.md`](skills/seo-geo-weekly/references/scheduling.md).

## What's inside

```
skills/seo-geo-weekly/
├── SKILL.md                    the loop: setup check, data, diagnosis, editing, gates, review, publishing, report
├── references/
│   ├── setup.md                first-time setup, step by step, per platform and DNS host
│   ├── consoles.md             reading Search Console, Bing Webmaster and clean SERPs through Chrome
│   └── scheduling.md           the weekly schedule
├── scripts/                    Python 3 + curl, no other dependencies
│   ├── audit_live.py           read-only technical + on-page audit of any live site
│   ├── verify_site.py          pre-publish gates for a folder of HTML (repo or build output)
│   ├── seo_checks.py           the shared page checks
│   ├── compare.py              this run's numbers vs the previous run's
│   ├── indexnow.py             tell Bing and others which pages changed
│   └── schedule.py             install / test / list / remove the weekly run
└── templates/
    ├── site.md                 the site profile (mode, authorization, rules, queries, sources)
    └── report.md               the weekly report
```

You can run the scripts on their own too:

```bash
python3 skills/seo-geo-weekly/scripts/audit_live.py https://www.example.com --max 40
python3 skills/seo-geo-weekly/scripts/verify_site.py ./public --site https://www.example.com
```

`audit_live.py` checks:
- that http/https/www variants redirect once;
- that missing pages return a real 404;
- robots.txt, including which AI crawlers are blocked;
- sitemaps and sitemap indexes, self-canonicals and noindex;
- titles and descriptions, h1, lang and alt text;
- that JSON-LD parses, with no dangling `@id`;
- that FAQPage text matches the visible FAQ.

## Requirements

- **Claude Code.**
- **Claude in Chrome,** so Claude can read Search Console and Bing for you. It needs:
  - a paid Claude plan that includes it;
  - Claude Code signed in with `/login`;
  - Chrome or another Chromium browser listed in the [official guide](https://code.claude.com/docs/en/chrome).

  Without the extension the skill still works: you export CSVs from the two consoles and Claude does the rest.
- **Accounts:** a Google account for Search Console, and a Microsoft, Google or Facebook account for Bing Webmaster Tools.
- **Access to your site:** wherever it is edited (a repo, or your CMS admin), and ideally your domain's DNS.
- **Python 3 and curl:**
  - macOS and most Linux have both;
  - on Windows, curl is built in; install Python from python.org and use `py` where the docs say `python3`.

## Principles

- **Nothing invented.** Every fact on your site comes from a source checked that day. AI assistants repeat wrong facts.
- **A few changes per week,** recorded, so you can tell what worked.
- **Your accounts stay yours.** Claude never types passwords or 2FA codes. Off-site changes (LinkedIn, GitHub profile, store listings) are listed for you to do.
- **Publishing follows your rules.** It publishes only what your site profile authorizes. Everything else is prepared and handed to you.
- **Your data stays on your machine,** in `~/seo/<your-domain>/` by default.

## Development

The scripts use only the standard library. To run the tests:

```bash
python3 -m unittest discover -s tests -v
```

CI runs them on Linux, macOS and Windows.

Issues and pull requests are welcome. Two rules for changes to the skill text:
- every rule should come from something that happened on a real site;
- every claim about a product (Search Console, Bing, a CMS) should be checked against its current documentation.

## License

[MIT](LICENSE)
