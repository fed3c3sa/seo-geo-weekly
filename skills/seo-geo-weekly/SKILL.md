---
name: seo-geo-weekly
description: SEO + GEO + AEO improvement loop for any website (static, WordPress, Shopify, Wix, Webflow...), from zero to a weekly data-driven routine. Walks the person through whatever is missing (Claude in Chrome, signing in, adding and verifying the site in Google Search Console and Bing Webmaster Tools, sitemaps, IndexNow), then each run reads the real numbers through Chrome, checks clean search results, audits the site, makes a handful of true changes, runs gates, publishes, requests indexing and writes a report; it can also schedule itself to run every week on the person's computer. Use when someone asks to "improve SEO", "do SEO/GEO", "show up on Google / in ChatGPT / in AI answers", "set up Search Console", "add my site to Bing", "why doesn't my site rank", "why don't I show up for my name or brand", "run the weekly SEO", "schedule the SEO every week", "analyze Search Console", "SEO audit", or the same in any language, even when they name only the domain.
---

# SEO / GEO / AEO loop, for any site

One loop, run about once a week:

1. Data
2. Diagnosis
3. A handful of true, verifiable changes
4. Gates
5. Publish
6. Indexing requests
7. Report

The first run also does the setup and guides the person through any step only they can do.

- **SEO:** rank in Google and Bing.
- **GEO:** be cited by AI assistants (Google AI Overviews and AI Mode, ChatGPT search, Microsoft Copilot, Perplexity, Claude). Bing's index feeds Copilot and is one of the sources behind ChatGPT search, so Bing matters more than its market share suggests.
- **AEO:** be the page that answers a question.

The levers overlap:
- true facts;
- clear entities (who or what the site is about, said the same way everywhere);
- questions answered in the first lines;
- links from the places that already rank;
- pages the crawlers can actually fetch.

The rules below come from real weekly runs on three kinds of site: an app's marketing site, an open-source project's site, and a personal site. Each rule is there because something happened.

**Files in this skill:**

| File | Use it for |
|---|---|
| `references/setup.md` | Step-by-step first-time setup, written to read aloud to a non-technical person: Claude in Chrome, sign-in, Search Console, Bing, IndexNow, per platform. |
| `references/consoles.md` | Reading Search Console and Bing Webmaster through Chrome: URLs, JavaScript snippets, quirks. |
| `references/scheduling.md` | Making the loop run every week on its own (launchd / cron / Task Scheduler), and why not cloud routines. |
| `templates/site.md` | The site profile to fill in on the first run. |
| `templates/report.md` | The weekly report. |
| `scripts/audit_live.py` | A read-only technical baseline plus an on-page audit of the live site, on any platform. |
| `scripts/verify_site.py` | Pre-push gates for a site you have as files (a repo or a build folder). |
| `scripts/indexnow.py` | Pings IndexNow for changed URLs. |
| `scripts/compare.py` | This run's numbers against the previous run's. |
| `scripts/schedule.py` | Installs, tests, lists and removes the weekly scheduled run. |

Run the scripts from this skill's base directory, `python3 <skill_dir>/scripts/...` (on Windows `py` instead of `python3`). They need only Python 3 and curl, and work on macOS, Linux and Windows.

## Ground rules (always)

- **Never sign in for the person and never type a password, a 2FA code or a recovery code.** Sign-ins, OAuth consent screens ("Allow Bing to access your Search Console data") and account choices are theirs. Open the page, say exactly what to click, wait, then check that it worked.
- **Never invent anything.** Every fact on the site must come from a primary source read that day. AI assistants repeat wrong facts, and a wrong fact sinks the page.
- **Stay inside what you're authorized to do** (section 0). Off-site accounts (social profiles, store listings, registries, shared repos) are the person's: list the steps, don't do them.
- **Use the person's language** in what you tell them. Write the site's copy in the site's language.
- **Small numbers are small.** A new site with 8 impressions in 28 days has no trends. Say so; don't invent them.

## 0. Start here: what is already in place?

On the first run, or when `site.md` is missing, check these in order. For each missing item, open `references/setup.md` at that step and walk the person through it, one step at a time, checking the result before moving on.

| # | Check | How you can tell |
|---|---|---|
| 1 | The site's canonical address, and how it is built and published (repo + host, or a CMS like WordPress/Shopify/Wix/Webflow/Squarespace) | Ask. Then run `audit_live.py <origin> --only-baseline`: it shows redirects, the server or CDN, robots.txt and sitemaps. |
| 2 | Claude in Chrome connected, in the Chrome profile that holds (or will hold) the webmaster accounts | Call `tabs_context_mcp`. If the browser tools are missing or fail, go to setup step A. |
| 3 | Signed in to Google in that profile | Open https://search.google.com/search-console?hl=en and read the account shown (avatar, top right). |
| 4 | The site in Search Console, verified | The property picker lists it; open it without "Ownership verification" prompts. Domain property preferred. |
| 5 | The sitemap submitted to Search Console | Sitemaps page shows "Success". |
| 6 | The site in Bing Webmaster Tools, verified, sitemap submitted | https://www.bing.com/webmasters lists it; tool pages don't say "User is unauthorized". |
| 7 | IndexNow | A key file at `<origin>/<key>.txt`, or a host or plugin that sends IndexNow by itself. |
| 8 | Where the edits happen | Repo access (`git`, `gh`) or the CMS admin, and whether a generator builds the pages. |
| 9 | A weekly schedule | `python3 <skill_dir>/scripts/schedule.py status`. If it's missing, offer it at the end of setup (section 11). |

Ask the person these, in one AskUserQuestion round if you can:
- **Mode:** may you change the copy, or only the technical layer (see "Two modes")?
- **Pushing:** may you publish SEO changes without asking each time?
- **House rules:** for example "no em dashes", wording that must or must not appear, a co-author who must always be credited.
- **The queries that matter:** their name, brand or product names, and the 3 to 6 questions their customers ask.
- **Known name collisions:** another company or person with the same name.

Write all of it into `site.md` (copy `templates/site.md`).

**Data folder.** Keep one folder per site, outside the site's repo. The default is `~/seo/<domain>/`; use another path if the person prefers.

```
~/seo/<domain>/
  site.md                       the profile, updated every run
  weekly/YYYY-MM-DD.md          one report per run (YYYY-MM-DD-checkin.md for check-ins)
  data/YYYY-MM-DD/28d/*.csv     totals, pages, queries, daily, targets
  data/YYYY-MM-DD/serp-clean.md clean-SERP notes
  data/YYYY-MM-DD/audit.txt     audit_live.py output
```

**Two modes, decided by the owner's words:**
- **Full mode:** pages, sections and copy may change. Every new sentence must still be true and sourced.
- **"Don't change the copy" mode:**
  - **Allowed:**
    - the `<head>`: title, description, canonical, robots, Open Graph, verification tags;
    - JSON-LD;
    - `rel=me` links;
    - alt text that describes what is already shown;
    - navigational links to the owner's own properties;
    - sitemap, robots.txt, llms.txt;
    - the IndexNow key, redirects, performance and accessibility fixes.
  - **Not allowed:** rewriting paragraphs, new sections, new claims, new numbers.
  - Even the allowed edits say only what the page already says.

If the owner says "don't ask, proceed", do everything inside the site and the webmaster tools. Then list the off-site steps for them with exact clicks.

## 1. First-time setup

Follow `references/setup.md`, which covers:
- **A. Claude in Chrome:** install it, connect it, choose the right profile, grant site permissions.
- **B. Signing in to Google.**
- **C. Search Console:**
  - the Domain or URL-prefix decision;
  - DNS TXT verification on common DNS hosts;
  - verification on WordPress, Shopify, Wix, Squarespace, Webflow, GitHub Pages, Netlify and Vercel;
  - the sitemap, the first indexing request, existing properties owned by someone else.
- **D. Bing Webmaster Tools:** import from Search Console, or add and verify by hand.
- **E. IndexNow:** a key file, or the host's or plugin's built-in support.
- **F. Files every site should have:** robots.txt, sitemap, llms.txt, a real 404 page.

Data starts 2 to 3 days after Search Console verification and up to 48 h after Bing. On day one the baseline is therefore `audit_live.py`, URL inspection and clean SERPs. Tell the person when the first real numbers will be there, and offer to note the date.

## 2. Pull the data (each run)

Details, URLs and JavaScript snippets are in `references/consoles.md`. The essentials:

- **Read with JavaScript, not screenshots:**
  - Use only visible tables (`offsetParent !== null`). Search Console is a single-page app that keeps stale tables in the DOM.
  - Keep each output under about 1 KB, or move it into the page and read it with `get_page_text`.
  - Strip `?`, `=` and `&` from any URL you print, or the output gets blocked.
- **Force English with `hl=en`,** so labels and number formats are predictable.
- **Google Search Console, 28 days** (`num_of_days=28`; the 3-month default overlaps 90% between weekly runs):
  - totals;
  - queries, pages, countries, devices;
  - `breakdown=date` for daily rows;
  - Page indexing, Sitemaps, Video indexing;
  - the AI features report, if the property shows it.
- **Bing Webmaster Tools:**
  - Search Performance;
  - **AI Performance** (Copilot citations, grounding queries, cited pages: the GEO report);
  - Site Explorer (what Bing actually crawled);
  - URL Inspection on key pages;
  - Recommendations, Site Scan, Backlinks.
- **Clean SERPs** (`pws=0`, explicit `gl` and `hl`, Bing with `cc=`):
  - the brand or name alone and with qualifiers;
  - the niche's head terms;
  - 3 to 6 long questions the site answers.
  - Trust these over a Search Console position for head terms. GSC positions include personalized searches: on one site GSC said 1.6 for its main head term, and the clean US results had it on neither page 1 nor 2. Break a head term down by country and page before believing it.
  - If Google shows "unusual traffic", stop. Never solve CAPTCHAs.
- **Technical:**
  - `audit_live.py <origin> --max 60 > data/<date>/audit.txt`;
  - Lighthouse when performance matters: `npx --yes lighthouse@12 <url> --quiet --chrome-flags="--headless=new" --only-categories=performance,seo,accessibility,best-practices --output=json --output-path=/tmp/lh.json`.

**Data files** use the same columns every run:
- `totals.csv`: window, clicks, impressions, ctr, position, ai_impressions, indexed_pages, indexed_videos
- `pages.csv`: page, clicks, impressions, ctr, position, ai_impressions
- `queries.csv`: query, clicks, impressions, ctr, position
- `daily.csv`: date, clicks, impressions, position
- `targets.csv`: query, target_page, baseline_position, baseline_source (what this run's changes aim at)

`python3 <skill_dir>/scripts/compare.py ~/seo/<domain>/data` prints the movement against the previous run: totals, pages, last run's targets and new queries.

## 3. Diagnose and choose (highest value first, a handful per run)

1. **Facts first.**
   - **When:** any page with impressions at position over 30.
   - **How:** check its claims against primary sources that week (the vendor's own help pages, the product's README or store listing).
   - **The case:** a guide said a feature didn't exist months after the vendor shipped it, and sat at position 58. After the fix it went from 44.7 to 22 in six days.
2. **Indexing and crawl problems:**
   - pages "Discovered, currently not indexed" or "Crawled, currently not indexed";
   - Google choosing a different canonical than declared;
   - soft 404s; http and https both live; redirect chains;
   - a sitemap listing redirected, noindex or non-canonical URLs;
   - robots.txt blocking a crawler the owner wants.
   - Bing may have crawled only a handful of pages (once 5 of 17), so request the rest.
3. **Entity and brand signals,** when a person, product or brand name is the main query.
   - **Ask:** do the places that already rank for the name link to the site? For a person: LinkedIn, GitHub, X, Medium, a store developer page. For a product: the app stores, GitHub, Product Hunt, social accounts. A page Google knows no link to (URL Inspection, "Referring page: None detected") will not rank for a name, however clean it is. Bing, which leans more on the page itself, may already rank it first.
   - **On the owner's own sites:** link between them (an author byline is natural). Write Person or Organization JSON-LD with:
     - `url`;
     - `sameAs`, with only profiles verifiably theirs;
     - `alternateName`, for handles and real alternate names;
     - `disambiguatingDescription`, from facts the page states;
     - `worksFor`, `alumniOf`, `knowsAbout`, as the page says.
   - **Reciprocal links:** products point at the person; the person's site points at the products.
   - **Name collisions:** know them and don't chase the other entity's results. Consistent naming plus `disambiguatingDescription` separates you.
4. **AI-answer (AEO) questions.**
   - **What they look like:** long "how do I…" queries in GSC, or Bing's grounding queries.
   - **The fix:** a section whose H2 is the question, answered in its first 40 to 60 words, then a short ordered list. Put the same question in the page FAQ and in FAQPage JSON-LD, with text identical to the visible answer.
   - **Where:** on the page Google already shows for that query.
5. **Near-duplicate queries at poor positions:** the page does not target that wording. Retitle it or rework the section; add a page only when the intent differs.
6. **Title and description:**
   - **When:** position 3 to 10 with CTR under about 3%.
   - **Limits:** title 65 characters or less, description 160 or less.
   - **Content:** lead with the words people search.
7. **New intents with real volume** (the "new queries" from `compare.py`): a guide or post modelled on the site's best page. Prefer a post when the query is broader than the product.
8. **Low-volume ideas:** log them in the backlog.

**Cadence:**
- **Attribution:** change at most a handful of things per run and record them in `targets.csv`, or the next run can't tell what worked.
- **Asked again within 7 days:** do a check-in only (recrawl dates, indexing errors), no content changes.
- **During a Google core update** (check https://status.search.google.com/): ship only small, verifiable fixes, then compare the week after it ends with the week before it began.

## 4. Edit safely

**Sites in a git repo:**
- **Where to work:**
  - Never in the owner's working checkout. It may be on another branch with uncommitted work.
  - Use a fresh worktree of the deploy branch, `git worktree add -b seo/$(date +%F) <dir> origin/main`, or a clean clone in a temp folder.
  - Commit with the identity the repo already uses (`git log -3 --format='%an <%ae>'`).
- **Generated pages:**
  - Edit the generator and its sources, never the output.
  - If you must patch output, patch the generator the same way. Then rebuild into a copy and `diff -rq` against your output; it must be identical.

**CMS sites** (WordPress, Shopify, Wix, Webflow, Squarespace):
- **Where:** in the admin, through Chrome, signed in by the owner.
- **Titles, descriptions and canonicals:** use the SEO fields (Yoast or Rank Math on WordPress, the page's "SEO settings" elsewhere) rather than theme code.
- **JSON-LD:** goes in the SEO plugin's schema settings or a custom-code-in-head field.
- **Before you change anything:** write the before and after of every field into the report, so it can be undone.

**Everywhere:**
- **Facts:**
  - Read every fact from its primary source that day: the README at the latest release tag, release notes, the package registry, the store listing, the paper, the CV, the vendor's help page.
  - Some help centers block curl (403), so read them in Chrome.
  - Paraphrase and link; don't paste long vendor text.
- **Dates:** bump `dateModified`, the visible "Updated" date and the sitemap `<lastmod>` on every page whose content changed. Use the real time of publishing, never an invented one. Markup-only fixes (alt text, schema) don't need a date bump.
- **House style:** apply the owner's rules everywhere: copy, meta, JSON-LD, alt text, llms.txt.
- **FAQ sync:** generate the visible answer and the JSON-LD answer from the same string.
- **Images:** when you change an `og:image`, rename the file; caches key on the URL.

## 5. Gates (all must pass before publishing)

```bash
# files you have locally (repo or build output):
python3 <skill_dir>/scripts/verify_site.py <site_root> --site https://www.example.com [--no-dashes] [--require "Co-author Name"] [--exclude drafts]
npx --yes html-validate@9 <changed .html files>       # compare the count with the version before your change
python3 -m http.server 8791 --directory <site_root>   # look at the changed spots in Chrome, narrow and wide
# any site, after publishing (or on a staging URL before):
python3 <skill_dir>/scripts/audit_live.py https://www.example.com --max 60
```

The checks:
- **Every page:**
  - title and description length, canonical, one h1, `<html lang>`, og tags;
  - img alt;
  - internal links and social images that resolve;
  - JSON-LD that parses, with no dangling `@id`s;
  - FAQPage matching the visible `<details>`;
  - the optional dash and required-text rules.
- **Site-wide:**
  - the sitemap parses, each URL maps to a page, and it lists only canonical, indexable URLs (each page's canonical must match its sitemap URL);
  - robots.txt doesn't block the whole site and has a `Sitemap:` line.
- **The live audit adds:**
  - redirect variants and a real 404;
  - `noindex` headers and self-canonicals;
  - AI crawlers blocked in robots.txt.

## 6. Independent review (a separate agent, never yourself)

Start a separate agent before publishing. If the owner prefers momentum ("publish, then fix"), start it in parallel with the push instead. Give it:
- the owner's rules, in their words;
- the diff (`git show <sha>`, or the before and after of CMS fields);
- the primary sources to check against, with exact URLs and commands;
- what to look for: facts, invented details, overstatements, schema validity, anything that hurts SEO;
- the format: MUST-FIX / SHOULD-FIX / verified, under 300 words.

What reviews have caught:
- **Invented details:** a made-up timestamp; a claim the vendor never made.
- **Wrong credit:** a co-author missing from an authorship statement.
- **Overstatements:** a plural where the source said one; a plan name that read as another company's plan; numbers taken from the wrong project.
- **A `sameAs`** that publicly tied the owner to something the site never mentions. Leave that call to the owner.

Apply MUST-FIX items in a follow-up change at once. Request indexing only after the fixes are live.

## 7. Publish and get crawled

```bash
git fetch -q origin && git log --oneline HEAD..origin/main   # must be empty, else rebase and re-run the gates
git add <files> && git commit   # message: what changed, and the numbers that motivated it
git push origin HEAD:main       # if the host answers 500, wait 15 s, retry, confirm with git ls-remote
```

Poll the live site with a cache-buster (`?n=$(date +%s)`) until the change shows. Then:
1. **Search Console:**
   - resubmit the sitemap;
   - request indexing for each changed URL: about 10 a day; the confirmation is "Indexing requested".
2. **Bing:**
   - resubmit the sitemap;
   - URL Inspection, then "Request indexing", for the same URLs;
   - read "SEO/GEO issues" on each while you're there.
3. **IndexNow:** `python3 <skill_dir>/scripts/indexnow.py <origin> <key> /changed/ /sitemap.xml /llms.txt`. Skip it if the host already sends IndexNow.
4. **Clean up:** remove the worktree and branch, stop the http.server, close the tabs you opened.

## 8. Report and what to tell the owner

**The report:** `weekly/YYYY-MM-DD.md`, from `templates/report.md`. Also write `targets.csv` and update `site.md`. If the person uses a memory or notes system, save one dated paragraph there.

**Tell the owner, in their language:**
- what the numbers say, including when they are too small to mean anything;
- what you changed and why;
- what to watch, and when;
- the off-site steps only they can do, as a short checklist.

## 9. Off-site work: list it, don't do it

These usually move rankings for a name or brand more than any on-page edit:
- the website field on LinkedIn (Contact info), GitHub (Settings, Public profile), X, Medium, Instagram, YouTube;
- the app store developer website, a Google Business Profile for local businesses;
- the Product Hunt maker profile, directories that matter in the niche;
- registries: PyPI project URLs, the npm `homepage`, Zenodo or ORCID;
- shared repos: the homepage field, README links;
- guest posts, talks, podcasts, partner pages that link back.

Each is the owner's account, or shared with others. Give exact steps and let them click. Do one yourself only when they explicitly say so for that item.

## 10. Pitfalls already paid for

- **Domain vs URL-prefix property:**
  - **Sitemap path:** a Domain property needs the full sitemap URL, or it says "invalid sitemap address"; a URL-prefix property takes `sitemap.xml`.
  - **Scope:** a URL-prefix property doesn't see the other protocol or host.
- **The direct `/inspect` link in Search Console 404s.** Type the URL into the top "Inspect any URL" box.
- **Never remove a verification file or tag after verifying.** The verification lapses.
- **GitHub Pages behind a proxied Cloudflare domain** can't issue its own certificate, so "Enforce HTTPS" stays off and `http://` stays live. Fix it in Cloudflare: SSL/TLS, Edge Certificates, "Always Use HTTPS".
- **Product facts change under you.** Re-check vendor facts every run, not only when writing.
- **A help center can be a single-page app** that answers 200 for any path. Check help links in a browser.
- **Other agents may share the same Chrome:** only touch tabs you opened.
- **Rich results:**
  - a ProfilePage `dateModified` must be a full ISO datetime, or Search Console flags it;
  - FAQ rich results now show only for some sites, but FAQPage still helps AI answers, so keep it in sync.
- **Lighthouse "mixed content"** on a form that posts to `mailto:` is functional, not an SEO issue.
- **Google rewrites snippets:** if the `site:` snippet looks wrong, check that the description is the first clear summary on the page before you rewrite anything.
- **A whole disk filled by Lighthouse or video builds:** check free space with `df` (on macOS, `du` miscounts cloned files).

## 11. Run it every week on its own

At the end of the first setup, offer to schedule the loop. Ask the day, the time and the permission level, then follow `references/scheduling.md`:

```bash
python3 <skill_dir>/scripts/schedule.py install example.com --day wed --time 10:07   # safe permissions by default
python3 <skill_dir>/scripts/schedule.py run example.com --test                       # 1-minute check, with them watching
```

- **Why this way:** it uses the computer's own scheduler (launchd, cron or Task Scheduler) to open a visible Claude Code session with Chrome each week.
- **Not cloud routines** (`/schedule`): they can't reach the person's Chrome, so they can't read Search Console or Bing.
- **Not `CronCreate` or `/loop`:** they die with the session, and recurring jobs expire after 7 days.
- **When a scheduled run starts this skill:** follow its prompt. Never wait on questions. Write blockers into the report and send the notification it gives.
