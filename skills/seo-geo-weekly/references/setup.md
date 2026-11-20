# First-time setup, step by step

Assume the person may be non-technical. Do one step at a time:
1. Say exactly what to click, in their language.
2. Wait for them.
3. Check the result yourself before the next step.

Do everything you can yourself: run commands, open pages, read values, edit files the person gave you access to. The person does only what needs their identity: signing in, consent screens, payments, and DNS or admin panels they haven't handed over.

**Never type a password, a 2FA code or a recovery code, and never ask for one in chat.** If they paste a secret, tell them not to and don't store it.

Menu names drift as products change. If a label below isn't there, look for the closest one on the page (`find` or `read_page`) or search the product's help for the task name. Don't guess.

---

## A. Claude in Chrome (lets you read Search Console and Bing for them)

**Check first:** call `tabs_context_mcp`. If it answers with tabs, the extension is connected. Skip to "Which Chrome profile".

**Requirements** (check before installing; the official guide, https://code.claude.com/docs/en/chrome, is the source of truth):
- **Browser:** Google Chrome, or another Chromium browser the guide lists, such as Edge or Brave.
- **Claude plan:** a paid plan that includes Claude in Chrome (Pro, Max, Team or Enterprise at the time of writing).
- **Login:** Claude Code signed in with `/login`, not an API key.
- **The same account:** the extension signed in to the same account or organization as Claude Code.
- **Windows:** not supported from inside WSL. Run Claude Code natively on Windows.

**If it isn't connected**, walk them through it:
1. **Install the extension.** In Google Chrome, open the Chrome Web Store, search for **"Claude"**, and install the extension published by **Anthropic**. Pin it with the puzzle-piece icon so it stays visible. The official guide is https://code.claude.com/docs/en/chrome.
2. **Sign in to it.** Click the Claude icon and sign in with the same Claude account they use here.
3. **Connect it to Claude Code.** Either:
   - quit and restart with `claude --chrome`;
   - or type `/chrome` in this session and turn it on.
4. **Check:** call `tabs_context_mcp` again. If it still fails, ask them to fully quit and reopen the browser once, then retry.

**Which Chrome profile.** Each Chrome profile is a separate set of Google accounts, and the extension works only in the profile where it is installed. Use the profile that holds, or will hold, the Google account that owns the site's Search Console.

- **Several profiles?** Ask which account owns (or should own) Search Console. Install the extension in that profile.
- **More than one browser connected?** Call `list_connected_browsers` and `select_browser`. Then confirm by opening Search Console and reading the account shown at the top right. Browser names like "Browser 1" change between sessions.
- **To open a specific profile:**
  - macOS: `open -na "Google Chrome" --args --profile-directory="Profile 2"`;
  - Windows: `"C:\Program Files\Google\Chrome\Application\chrome.exe" --profile-directory="Profile 2"`;
  - `chrome://version` shows a profile's folder name ("Profile Path").

**Site permissions.** The extension asks before it acts on a new site. If a navigation silently stays on "New Tab", or a page never loads, the extension is waiting for approval. Ask them to click the Claude icon and allow:
- `search.google.com`
- `www.google.com`
- `www.bing.com`
- their own site
- their DNS host or CMS admin, if you will work there

**If Claude in Chrome isn't available** (plan, company policy, another browser), use the manual route in section G. Everything else in the skill still works.

---

## B. Signed in to Google

Open https://search.google.com/search-console?hl=en in that profile.

| What you see | What it means |
|---|---|
| A sign-in page | They sign in themselves. Wait, then check the account shown at the top right. |
| A property list or a "Welcome" page | They're signed in. Check it's the right account: properties live under the account that verified them. |

**If the site may already be in Search Console under another account** (a developer's, an agency's, a colleague's):
1. Ask that person to open Settings, then "Users and permissions":
   - **"Add user"** with Full permission: enough for everything in this skill;
   - **"Manage property owners"**: to make this account an owner too.
2. Or verify again with this account. Several owners per property are fine.

---

## C. Google Search Console

### C1. Choose the property type

| Type | Covers | Verified by | Choose it when |
|---|---|---|---|
| **Domain** (`example.com`) | http, https, www, every subdomain | a DNS TXT record | they (or you, with access) can edit DNS. **Preferred.** |
| **URL prefix** (`https://www.example.com/`) | that exact protocol and host only | an HTML file, a meta tag, Google Analytics, Tag Manager, or DNS | DNS is out of reach, or the platform has a built-in verification field |

Open https://search.google.com/search-console/welcome?hl=en. Or, from an existing account, open the property picker, then "Add property".

### C2. Find who serves DNS (for a Domain property)

```bash
dig +short NS example.com          # macOS / Linux
nslookup -type=NS example.com      # Windows
```

| Nameservers end in | DNS is at |
|---|---|
| `ns.cloudflare.com` | Cloudflare |
| `domaincontrol.com` | GoDaddy |
| `registrar-servers.com` | Namecheap |
| `wixdns.net` | Wix |
| `shopify.com` | Shopify |
| `squarespacedns.com` / `googledomains.com` | Squarespace Domains |
| `vercel-dns.com` | Vercel |
| `nsone.net` | Netlify or Squarespace (check which they use) |
| `awsdns` | AWS Route 53 |
| anything else | that provider (search the name) |

The DNS host is not always where the domain was bought. Edit the record where the nameservers point.

### C3. Verify a Domain property with a TXT record

Search Console shows a value like `google-site-verification=AbC123...`. Copy it with the page's Copy button, or read it with JavaScript. Then add a TXT record on the DNS host:

| Field | Value |
|---|---|
| Type | TXT |
| Name / Host | `@` (some panels want it blank, or the bare domain) |
| Value / Content | the whole `google-site-verification=...` string |
| TTL | default / Auto |

Where to add it, per DNS host:
- **Cloudflare:** pick the domain, then DNS, Records, "Add record".
  - TXT records have no orange-cloud proxy setting, so nothing else to choose.
  - If the form fights you, use "Import and Export", then "Import DNS records", with a one-line file: `example.com. 300 IN TXT "google-site-verification=..."`.
- **GoDaddy:** My Products, then the domain, DNS (or "Manage DNS"), then "Add New Record".
- **Namecheap:** Domain List, then Manage, Advanced DNS, "Add new record", "TXT Record", host `@`.
- **Wix:** Domains, then the domain's "⋯" menu, "Manage DNS records", the TXT section.
- **Shopify:** Settings, then Domains, the domain, "DNS settings", "Add custom record", TXT.
- **Squarespace Domains:** Domains, then the domain, "DNS", "Custom records", TXT.
- **Other hosts:** search their help for "add TXT record".
- **One-click option:** for some providers Search Console offers "Start verification", which signs into the provider for you. The person does that login.

Then wait 2 to 10 minutes and press **Verify**. Check from your side meanwhile: `dig +short TXT example.com` should list the value. DNS can take up to a day, but usually takes minutes. If Verify fails and `dig` shows the record, wait 10 minutes and retry. Never delete the record afterwards.

### C4. Verify a URL-prefix property, per platform

**HTML file** (sites from a repo: GitHub Pages, Netlify, Vercel, Cloudflare Pages, any static host):
1. Download `googleXXXXXXXX.html` from Search Console.
2. Put it at the site root, commit, deploy.
3. Check that `curl -s https://www.example.com/googleXXXXXXXX.html` returns it, then press Verify.
4. Keep the file forever.

**Meta tag** (`<meta name="google-site-verification" content="...">` in the home page `<head>`), per platform:
- **WordPress:**
  - Yoast SEO: Yoast SEO, then Settings, "Site connections", the Google field (paste only the content value);
  - Rank Math: Rank Math, then General Settings, "Webmaster Tools";
  - or install Google's **Site Kit** plugin, which verifies and connects Search Console through a Google sign-in (the person clicks).
- **Shopify:** Online Store, then Themes, "⋯", "Edit code", `layout/theme.liquid`. Paste the tag just before `</head>` and save. Or use the Domain property via Shopify DNS (C3).
- **Wix:** Marketing & SEO (or "SEO"), then "SEO Tools" / "Tools and settings", "Site verification", Google. Wix's own SEO setup checklist can also connect Search Console with a Google sign-in.
- **Squarespace:** the built-in Search Console connection. Search Squarespace help for "Google Search Console" for the current menu path. Or the Domain property via DNS.
- **Webflow:** Site settings, then SEO, the "Google site verification" field. Then publish the site.
- **Ghost:** Settings, then "Code injection", Site header.
- **Anything else:** a "custom code in head" or "header scripts" setting, or the Domain property.

After the tag is live (check with `audit_live.py <origin> --only-baseline`, which reports it), press Verify.

### C5. Right after verifying

1. **Submit the sitemap.** Open Sitemaps in the left menu.
   - **Domain property:** type the full URL, `https://www.example.com/sitemap.xml`. A relative path gives "invalid sitemap address".
   - **URL-prefix property:** type `sitemap.xml`.
   - **Where the sitemap usually is:**

     | Platform | Sitemap URL |
     |---|---|
     | WordPress core | `/wp-sitemap.xml` |
     | Yoast or Rank Math | `/sitemap_index.xml` |
     | Shopify, Wix, Squarespace, Ghost | `/sitemap.xml` |
     | Webflow | `/sitemap.xml`, once "Auto-generate sitemap" is on in SEO settings |
     | Static sites | whatever the generator writes; `audit_live.py` reads the `Sitemap:` line in robots.txt |

2. **Request indexing for the home page.** Type the home URL into the top "Inspect any URL in…" box and press Enter. Wait about 15 seconds, then click "REQUEST INDEXING" and wait for "Indexing requested".
3. **Say when data will come:** performance data starts in 2 to 3 days and always lags about 2 days.

---

## D. Bing Webmaster Tools (feeds Copilot and ChatGPT search)

Open https://www.bing.com/webmasters. The person signs in with a Microsoft, Google or Facebook account. A Google sign-in with the same account as Search Console is simplest.

**Fastest: import from Google Search Console.**
1. Choose "Import your sites from GSC".
2. Google's consent screen appears. The person clicks Allow; it's their consent.
3. Tick the sites and press Import.

Imported sites come verified, with their sitemaps.

**Or add the site by hand:**
1. "Add your site manually", with the exact canonical URL (`https://www.example.com/`).
2. Choose a verification method:
   - **XML file:** upload `BingSiteAuth.xml` to the site root. Static sites only.
   - **HTML meta tag:** `<meta name="msvalidate.01" content="...">` in the home page `<head>`. Put it where the Google tag went (Yoast and Rank Math have a Bing field). Read the value from the panel with JavaScript instead of copying it by hand.
   - **CNAME record:** on the DNS host, as in C3.
3. **"Skip & verify later"** adds the site unverified. Deploy the tag, then select the site and press Verify. Until then every tool page says "User is unauthorized to access the site".
4. Never remove the tag or file after verifying.

**Then:**
1. Sitemaps, then "Submit sitemap", with the full URL.
2. URL Inspection: enter the home page, Inspect, then "Request indexing" and Submit. The daily quota shows in the dialog.
3. Reports fill in within about 48 hours. The "AI Performance" report (Copilot citations) may take longer on a small site.

---

## E. IndexNow (tells Bing, Yandex, Seznam, Naver at once that a page changed)

**Check first whether the host already does it:**
- **Cloudflare:** Caching, then Configuration, "Crawler Hints", on. This sends IndexNow automatically, but only when the domain is proxied through Cloudflare (orange cloud).
- **WordPress:** Rank Math has IndexNow built in, Yoast SEO Premium sends it too, or use Microsoft's "IndexNow" plugin.
- **Wix:** sends IndexNow automatically on Premium plans with a connected domain.

If any of these is on, record it in `site.md` and skip the rest.

**Static sites and repos:**

```bash
KEY=$(python3 -c "import secrets;print(secrets.token_hex(16))")
printf "%s" "$KEY" > "<site_root>/$KEY.txt"     # commit + deploy
python3 <skill_dir>/scripts/indexnow.py https://www.example.com "$KEY" / /sitemap.xml   # 200 or 202 = accepted
```

On Windows (PowerShell), make the key with `py -c "import secrets;print(secrets.token_hex(16))"` and save it, with no newline, as `<key>.txt` in the site root.

Record the key in `site.md`. It isn't a secret, because it's public by design.

---

## F. Files every site should have

| File | What it holds | Notes |
|---|---|---|
| `robots.txt` | `User-agent: *`, `Allow: /`, a `Sitemap:` line with the full URL | Never block Googlebot or Bingbot. AI search and answer crawlers (OAI-SearchBot, ChatGPT-User, Claude-SearchBot, Claude-User, PerplexityBot, Perplexity-User): blocking them keeps the site out of those assistants' answers; leave them allowed unless the owner wants that. Some user-triggered fetchers may not follow robots.txt at all. Training crawlers (GPTBot, ClaudeBot, Applebot-Extended, CCBot) are the owner's choice and don't affect search ranking. Google-Extended is a control, not a crawler: blocking it stops Gemini training and grounding in Gemini apps and Vertex AI, but doesn't affect Google Search or AI Overviews. Editing it: Shopify `robots.txt.liquid`; Wix "Robots.txt editor"; WordPress via the SEO plugin. |
| `sitemap.xml` | Canonical, indexable URLs only (no redirects, no noindex), with real `<lastmod>` | Most CMSs generate it. |
| `llms.txt` | A short markdown summary for AI assistants: one line on what the site or person is, key facts with sources, links to the main pages | A proposed standard (llmstxt.org) that few crawlers are confirmed to read. Cheap to add; optional. |
| a real 404 | Missing pages answer HTTP 404 with a helpful page | `audit_live.py` checks this. A "200 page not found" is a soft 404. |
| one canonical origin | http/https and www/apex all 301 once to the same origin | `audit_live.py` checks this. Fix it at the host or CDN ("Always Use HTTPS", a redirect rule). |

---

## G. Without Claude in Chrome: manual exports

If you can't drive the browser, the person exports the data and you do everything else.

1. **Search Console:** Performance, then "Search results", "Last 28 days". Click **Export**, then "Download CSV", once per tab: Queries, Pages, Countries, Devices, Dates. Also export Page indexing, then "Export".
2. **Bing:** Search Performance, then the Download icon on the Keywords and Pages tabs. Also AI Performance, if it has data.
3. **Saving:** have them save the files into `~/seo/<domain>/data/YYYY-MM-DD/raw/`. Convert them to the skill's CSV columns.
4. **Indexing requests:** give them the exact list of URLs to paste into URL Inspection, on both consoles.

For automation later, both consoles have APIs (the Search Console API with a Google Cloud service account added as a user; the Bing Webmaster API with an API key from Settings). Set them up only if the person asks; the keys are secrets and stay in their environment.

---

## Setup done: confirm before the first run

Before the first run, confirm each of these:
- [ ] Claude in Chrome connected, in the right profile and account (or the manual route agreed).
- [ ] Search Console property verified. Domain type, or URL prefix on the canonical origin.
- [ ] Sitemap submitted in Search Console: status "Success".
- [ ] Home page indexing requested.
- [ ] Bing site verified, sitemap submitted, home page indexing requested.
- [ ] IndexNow: key file live, or a host or plugin sending it.
- [ ] `audit_live.py --only-baseline` clean, or its problems listed for the first run.
- [ ] `site.md` written: mode, authorization, house rules, the queries that matter, collisions.
- [ ] The person knows when the first numbers will arrive (about 3 days). Offer to run the first full pass then.
- [ ] Weekly schedule offered: installed and `--test` passed, or declined (`references/scheduling.md`).
