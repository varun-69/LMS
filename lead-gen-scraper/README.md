# Lead Gen Scraper 🗺️ → 📋

A **free** lead-generation web app. Type a niche and a location (e.g. *“web development” in “Dubai”*),
and it scrapes matching businesses from **Google Maps**, finds their **phone, website, rating, email and
WhatsApp number**, shows them in a live table, and lets you **export to Excel or WhatsApp**.

No paid APIs, no API keys. It drives a real headless Chromium under the hood (via Playwright), so it
runs on your own machine for free.

---

## ✨ What you get per lead

| Field | Source |
|---|---|
| Business name, category, address | Google Maps |
| Phone | Google Maps |
| Website | Google Maps |
| Rating + review count | Google Maps |
| Email | Scraped from the business website (mailto / contact page) |
| WhatsApp number | `wa.me` / `api.whatsapp.com` links on the website |
| Other phones (often mobiles) | `tel:` links on the website |

> **About “decision-maker numbers”:** Google Maps only exposes the *business’s* listed contact. The
> direct mobile of an owner/decision-maker is **not** available for free — that requires a paid data
> provider (Apollo, Lusha, LinkedIn Sales Nav, etc.). This app gathers the business phone plus any
> mobile/WhatsApp numbers published on the company website, which is the most you can get for free.

---

## 🚀 Quick start

```bash
# 1. install dependencies (also downloads the Chromium browser)
npm install

# 2. start the app
npm run dev

# 3. open http://localhost:3000
```

If the browser didn’t download automatically, run it manually once:

```bash
npx playwright install chromium
```

Then in the UI:

1. Enter your **niche** (e.g. `digital marketing`, `dentists`, `gyms`).
2. Enter the **area** (`London`, `Dubai`, `Bangalore`, or even a whole country).
3. Set **max results** and hit **Find leads**. Rows stream in live.
4. Click **Export Excel** for an `.xlsx`, or **Export to WhatsApp (.vcf)** to get a contacts file you
   can import into your phone — they’ll then be reachable in WhatsApp. Each row also has a **Chat ↗**
   button that opens a `wa.me` chat directly.

---

## 🧱 How it works

```
app/page.tsx            → UI: search form, live table, export buttons
app/api/scrape/route.ts → streams NDJSON results as they’re scraped
lib/scraper.ts          → Playwright: searches Maps, scrolls, opens each listing
lib/enrich.ts           → fetches each website for email / WhatsApp / phones
lib/export.ts           → Excel (.xlsx) + WhatsApp (.vcf + wa.me links)
```

Results are streamed one-by-one so the table fills up as the scrape runs, and you can **Stop** at any time.

---

## ⚖️ Use responsibly

This tool reads publicly visible business listings. Scraping Google Maps is against Google’s Terms of
Service, and aggressive use can get your IP rate-limited. Keep result counts reasonable, don’t hammer it,
and respect local data/marketing laws (GDPR, CAN-SPAM, India DND, etc.) and WhatsApp’s policies when you
contact leads. You are responsible for how you use the collected data.

---

## 🛠️ Tech

Next.js 14 (App Router) · TypeScript · Playwright · Cheerio · Tailwind CSS · SheetJS (xlsx).
