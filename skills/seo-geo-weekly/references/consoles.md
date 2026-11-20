# Reading Search Console, Bing Webmaster and clean SERPs through Chrome

## Browser mechanics (Claude in Chrome)

- **Check the account before reading anything.** Read the avatar or account at the top right. The extension's browser names drift between sessions.
- **Read with JavaScript, not screenshots.** Screenshots misread numbers, and they cost far more.
- **Output limits:** the JavaScript tool's output caps at about 1 KB. For long tables, do one of these:
  - store rows in `window.__rows` and read about 850-character chunks, split at row boundaries;
  - prepend an `<article>` built with `document.createElement` + `textContent` (Search Console enforces TrustedHTML, so `innerHTML` throws), one `<p>` per row, then call `get_page_text`.
- **Output with a URL query string gets blocked** ("cookie/query string data"). Print hostname + path only, or replace `?`, `=` and `&` before returning.
- **Never `fetch()` to localhost from a page.** Chrome's local-network permission prompt hangs the tab.
- **Keep browser batches short.** Several navigations with long waits time out the whole batch, so do one navigation plus one read per call. Waits are capped (about 10 s each), so chain two for slow panels.
- **Blank pages:** Search Console sometimes renders blank after you arrive from another domain. Navigate to the same URL again.
- **Clean up:** only touch tabs you opened, and close them at the end. Other agents or the person may be using the same browser.

## Google Search Console

**Base URL** (add `&hl=en` to every Search Console URL):

```
https://search.google.com/search-console/performance/search-analytics?resource_id=<RID>&hl=en&metrics=CLICKS%2CIMPRESSIONS%2CCTR%2CPOSITION
```

What goes in `<RID>`:
- **Domain property:** `sc-domain%3Aexample.com`.
- **URL-prefix property:** the encoded URL, `https%3A%2F%2Fwww.example.com%2F`.

| Add | Gets |
|---|---|
| `&num_of_days=28` | the 28-day window, used for run-over-run comparison |
| `&start_date=YYYYMMDD&end_date=YYYYMMDD` | a custom window, e.g. the days since a change shipped |
| `&breakdown=page` / `country` / `device` / `date` | that breakdown (none = queries). `date` gives daily rows for exact before/after windows |
| `&page=!<encoded exact URL>` | one page; with no breakdown it lists that page's queries |
| `&query=!<encoded query>` | one exact query; combine with `breakdown=page` or `country` |
| `.../search-analytics/ai?resource_id=...` | AI features report (AI Overviews / AI Mode), where the property has it |
| `.../index?resource_id=...` | Page indexing (why pages are not indexed) |
| `.../sitemaps?resource_id=...` | Sitemaps |
| `.../video-index?resource_id=...` | Video indexing |

**Totals:** read `document.body.innerText` for "Total clicks", "Total impressions", "Average CTR" and "Average position". Numbers use compact formats (`1.64K`, `6.7%`).

**Rows:** set "Rows per page" to 500 once; it persists. Then read the visible table:

```js
const vis=[...document.querySelectorAll('table')].filter(t=>t.offsetParent!==null)[0];
window.__rows=[...vis.querySelectorAll('tbody tr')].map(r=>[...r.querySelectorAll('td')].map(td=>td.innerText.trim().replace(location.origin,'')).join('|'));
window.__rows.length+'\n'+window.__rows.slice(0,25).join('\n').replace(/https?:\/\/[^/|]+/g,'')
```

**URL inspection:**
1. Type the URL into the top box, "Inspect any URL in …", and press Enter. Never use a direct `/inspect` link; it 404s.
2. Wait about 15 s, then expand "Page indexing".
3. Read:

| Field | Tells you |
|---|---|
| "Last crawl" | which version Google has |
| "User-declared canonical" vs "Google-selected canonical" | they must match |
| "Referring page" | "None detected" means Google knows no page that links here (an entity and brand problem) |
| "Crawl allowed?" / "Indexing allowed?" | whether robots.txt or noindex stops it |

**Request indexing:**
1. Click "REQUEST INDEXING".
2. Wait up to 20 s for "Indexing requested".
3. Close the dialog. Find the close button with `find`; coordinates drift.

The quota is about 10 a day per property.

## Bing Webmaster Tools

URLs take the form `https://www.bing.com/webmasters/<tool>?siteUrl=<origin>/`.

| Tool | What to read |
|---|---|
| `searchperf` | Search Performance: totals, then the Keywords, Pages and Country tabs. Defaults to 3 months; pick 1 month to match the 28-day window. |
| `aiperformance` | **The GEO report.** Citations in Microsoft Copilot and partners, **Grounding queries** (what Copilot answered using your pages, with citation share) and cited **Pages**. |
| `siteexplorer` | Which URLs Bing has actually crawled and indexed, and when. "Discovered but not crawled" means request them. |
| `urlinspection` | Per-URL index status, "SEO/GEO issues", "Request indexing" (the daily quota shows in the dialog). |
| `sitemaps` | Submitted sitemaps; the row menu has "Resubmit". |
| `seoreports` | Recommendations: site-wide SEO errors by severity. |
| `sitescan` | An on-demand audit. Start one on the sitemap each run; read it next run. |
| `backlinks` | Referring domains. |
| `keywordresearch` | Bing search volumes and the top 10 URLs for a term. |

**Reading the tables:**
- They are Fluent UI DetailsLists. Read `.ms-DetailsRow` cells (`[role=rowheader]`, `[role=gridcell]`) after scrolling them into view.
- Search Performance pages 25 rows at a time.
- Strip `?`, `=` and `&` from what you print.

```js
[...document.querySelectorAll('.ms-DetailsRow')].map(r=>[...r.querySelectorAll('[role=rowheader],[role=gridcell]')].map(c=>c.innerText.trim()).join('|')).join('\n').replace(/[?=&]/g,' ').slice(0,900)
```

## Clean SERPs

**Why:** Search Console positions include personalized and local searches. For head terms, check what a neutral searcher sees.

**Google:** `https://www.google.com/search?q=<query>&pws=0&gl=us&hl=en`:
- use the site's main market instead of `us`/`en` (e.g. `gl=it&hl=it`);
- `&start=10` for page 2;
- `&udm=50` for AI Mode.

```js
[...document.querySelectorAll('#rso a h3, #search a h3')].map(h=>{const a=h.closest('a');let u;try{u=new URL(a.href)}catch(e){return ''}return u.hostname+u.pathname.slice(0,50)+' :: '+h.innerText.slice(0,60)}).join('\n')
```

Also read the AI Overview text if one shows, and note whether the site is cited in it.

**Bing:** `https://www.bing.com/search?q=<query>&cc=us`. Links are redirects, so read the visible hostnames:

```js
[...document.querySelectorAll('#b_results li.b_algo')].map(li=>(li.querySelector('cite')||{}).innerText+' :: '+((li.querySelector('h2')||{}).innerText||'').slice(0,60)).join('\n').replace(/[?=&]/g,' ')
```

**`site:example.com`** shows which pages Google has and the title and snippet it actually uses.

**Which queries:**
- the brand or name alone, then with qualifiers (name + role, + city, + product);
- the niche's head terms;
- 3 to 6 long questions the site answers.

**Write `serp-clean.md`:** the ranked hostnames per query, marking which results are the owner's (their site, their profiles) and which belong to namesakes.

**If "unusual traffic" or a CAPTCHA appears:** stop searching for this run. Never solve it.

**AI assistants directly:** ask ChatGPT, Perplexity or Copilot the key questions in the browser only if the person is signed in and agrees. Note whether the site is cited. Don't treat one answer as a trend.
