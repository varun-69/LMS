# Lead Gen Scraper 🗺️📡 → 📋

A **free** lead-generation web app for freelancers & agencies. Two things in one:

1. **Maps Leads** — type one or more niches + a location (e.g. *“web development, SEO, digital marketing” in “Dubai”*) and it scrapes matching businesses from **Google Maps**: phone, website, rating, address, plus **email & WhatsApp** found on their websites. Filter, then export to **Excel** or **WhatsApp**.
2. **Intent Radar** — find people *asking for your service right now*. Pulls live buying-intent posts from **Reddit** (free API) and gives one-click **intent-search links** for LinkedIn / X / Instagram / Threads / Naukri / Google / Facebook.

On any lead or post, hit **✨ Draft** and **Claude** writes a personalized email + WhatsApp + DM (with your booking link) that you review and send.

No paid scraping APIs. Runs on your machine via a headless Chromium. The only optional paid bit is an Anthropic API key for the AI drafting (everything else is free).

---

## ✨ Features

- **Multiple niches at once** — comma-separated; results are de-duplicated and each lead is tagged with the niche it matched.
- **Filters** — No-website / Has-website, minimum rating, has-email, has-WhatsApp. No-website businesses are kept and badged (often your best prospects for web/marketing work).
- **Per-lead data** — name, category, rating + reviews, phone, website, address, emails, WhatsApp numbers.
- **Resilient enrichment** — when a business site is JS-heavy or blocks plain scrapers, it falls back to **Jina Reader** (`r.jina.ai`, free, no key) to still pull emails & WhatsApp. (Inspired by the [agent-reach](https://github.com/Panniantong/agent-reach) toolkit.)
- **Intent Radar** — buying-intent posts from the last 24h / 7d / 30d, aggregated across **Reddit + Hacker News + a web-wide search (Jina)**, with **Exa** semantic results too if you add a key. Each result is source-tagged. Plus one-click pre-filtered search links for platforms that can’t be read for free (LinkedIn, X, Instagram, Threads, Naukri, Google, Facebook).
- **AI outreach (Claude)** — personalized email/WhatsApp/DM drafts, editable, with your booking link woven in. **You send them yourself.**
- **Exports** — `.xlsx` spreadsheet and `.vcf` contacts (import into your phone → reachable in WhatsApp). Each row also has a `wa.me` chat button.

---

## 🚫 What this intentionally does NOT do (and why)

- **It does not log into your LinkedIn / Instagram / Naukri accounts to scrape or auto-DM.** Automating a logged-in personal account violates those platforms’ Terms of Service and is the fastest way to get your account **permanently banned**. There is no free, stable, safe way to do it. Instead, the Intent Radar opens each platform’s *own* search (where you’re already logged in) pre-filtered to buying-intent posts.
- **It does not auto-send messages or auto-book meetings.** Mass automated outreach is spam and exposes you to anti-spam law (GDPR, India DND, WhatsApp policy) and reputation damage. The safe, fast alternative is here: Claude drafts the message in seconds, you glance and send.
- **It can’t get “decision-maker” personal mobiles for free.** Google Maps lists the *business* contact only. Direct owner lines need a paid data provider (Apollo, Lusha, LinkedIn Sales Nav).

---

## 🚀 Quick start

```bash
npm install            # also downloads the Chromium browser
npm run dev            # open http://localhost:3000
```

If the browser didn’t download automatically: `npx playwright install chromium`.

### Optional: enable AI drafting

```bash
cp .env.example .env.local
# then set ANTHROPIC_API_KEY=...  (get one at https://console.anthropic.com)
npm run dev
```

The Maps scraping, Reddit intent, search links, and exports all work **without** any API key — only the ✨ Draft button needs one. Model defaults to `claude-opus-4-8`; set `ANTHROPIC_MODEL=claude-haiku-4-5` for cheaper bulk drafting.

---

## 🧱 How it works

```
app/page.tsx              → UI: shared inputs, tabs, filters, exports
app/api/scrape/route.ts   → streams NDJSON Maps results as they’re scraped
app/api/intent/route.ts   → Reddit intent search + intent-link builder
app/api/draft/route.ts    → Claude writes outreach (needs ANTHROPIC_API_KEY)
lib/scraper.ts            → Playwright: multi-niche Maps search + extract
lib/enrich.ts             → fetch each website for email / WhatsApp / phones
lib/reddit.ts             → free Reddit JSON search for buying-intent posts
lib/intentLinks.ts        → pre-filtered search URLs per platform
lib/export.ts             → Excel (.xlsx) + WhatsApp (.vcf + wa.me links)
components/                → LeadsTable, IntentRadar, DraftDialog
```

---

## ⚖️ Use responsibly

Scraping Google Maps is against Google’s Terms of Service, and aggressive use can get your IP rate-limited — keep result counts reasonable. Respect local data/marketing laws (GDPR, CAN-SPAM, India DND) and WhatsApp’s policies when contacting leads. You are responsible for how you use the collected data.

---

## 🛠️ Tech

Next.js 14 (App Router) · TypeScript · Playwright · Cheerio · Tailwind CSS · SheetJS (xlsx) · Anthropic SDK (Claude).
