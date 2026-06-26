import { chromium, type Browser, type Page } from "playwright";
import { enrichFromWebsite } from "./enrich";
import type { Business, ScrapeParams } from "./types";

const MAPS_SEARCH = "https://www.google.com/maps/search/";

type OnBusiness = (b: Business) => void | Promise<void>;
type OnStatus = (message: string) => void;

const sleep = (ms: number) => new Promise((r) => setTimeout(r, ms));

/** Try to clear Google's cookie-consent interstitial (mostly EU traffic). */
async function acceptConsent(page: Page): Promise<void> {
  try {
    const url = page.url();
    if (!url.includes("consent.")) return;
    const btn = page.locator(
      'button[aria-label*="Accept all"], button:has-text("Accept all"), form[action*="consent"] button',
    );
    if (await btn.first().isVisible({ timeout: 3000 }).catch(() => false)) {
      await btn.first().click();
      await page.waitForLoadState("domcontentloaded");
    }
  } catch {
    /* best effort */
  }
}

/** Scroll the results feed until we have enough place links or it stops growing. */
async function collectPlaceLinks(page: Page, limit: number, onStatus: OnStatus): Promise<string[]> {
  const seen = new Set<string>();
  let stagnant = 0;

  for (let i = 0; i < 60; i++) {
    const links = await page
      .$$eval("a.hfpxzc", (els) => els.map((e) => (e as HTMLAnchorElement).href))
      .catch(() => [] as string[]);

    for (const href of links) seen.add(href);
    onStatus(`Found ${seen.size} businesses so far…`);

    if (seen.size >= limit) break;

    // Reached the end of the list?
    const ended = await page
      .locator('text=/reached the end of the list/i')
      .count()
      .catch(() => 0);
    if (ended > 0) break;

    const before = seen.size;
    await page.evaluate(() => {
      const feed = document.querySelector('div[role="feed"]');
      if (feed) feed.scrollBy(0, feed.scrollHeight);
    });
    await sleep(1600);

    if (seen.size === before) {
      stagnant += 1;
      if (stagnant >= 4) break;
    } else {
      stagnant = 0;
    }
  }

  return [...seen].slice(0, limit);
}

/** Extract the structured fields from an open Google Maps place panel. */
async function extractDetail(page: Page): Promise<Omit<Business, "id" | "mapsUrl" | "niche" | "emails" | "whatsapp" | "sitePhones">> {
  await page.waitForSelector("h1", { timeout: 15000 }).catch(() => {});
  return page.evaluate(() => {
    const txt = (sel: string) => document.querySelector(sel)?.textContent?.trim() || "";

    const name =
      document.querySelector("h1.DUwDvf")?.textContent?.trim() ||
      txt("h1") ||
      "";

    let rating = "";
    let reviews = "";
    const ratingBox = document.querySelector("div.F7nice");
    if (ratingBox) {
      rating = ratingBox.querySelector('span[aria-hidden="true"]')?.textContent?.trim() || "";
      const revMatch = ratingBox.textContent?.match(/\(([\d.,]+)\)/);
      reviews = revMatch ? revMatch[1].replace(/[.,]/g, "") : "";
    }

    const category =
      document.querySelector('button[jsaction*="category"]')?.textContent?.trim() || "";

    const address =
      document
        .querySelector('button[data-item-id="address"]')
        ?.getAttribute("aria-label")
        ?.replace(/^Address:\s*/i, "")
        .trim() || "";

    let phone = "";
    const phoneBtn = document.querySelector('button[data-item-id^="phone:tel:"]');
    if (phoneBtn) {
      phone = (phoneBtn.getAttribute("data-item-id") || "").replace("phone:tel:", "").trim();
    }

    let website = "";
    const siteEl = document.querySelector('a[data-item-id="authority"]') as HTMLAnchorElement | null;
    if (siteEl) website = siteEl.href;

    return { name, rating, reviews, category, address, phone, website };
  });
}

function placeIdFromUrl(url: string): string {
  const m = url.match(/!1s([^!]+)/) || url.match(/place\/([^/]+)/);
  return m ? m[1] : url;
}

/**
 * Scrape Google Maps for a niche in a location. Streams each business out via
 * `onBusiness` as soon as it is parsed (and optionally enriched), so the UI can
 * render results progressively. Uses only a headless browser — no API keys.
 */
export async function scrapeGoogleMaps(
  params: ScrapeParams,
  onBusiness: OnBusiness,
  onStatus: OnStatus = () => {},
  signal?: AbortSignal,
): Promise<number> {
  const { niches, location, limit, enrich } = params;

  let browser: Browser | null = null;
  let count = 0;
  // Dedupe across niches — the same business can match several searches.
  const seenIds = new Set<string>();

  try {
    onStatus("Launching headless browser…");
    browser = await chromium.launch({
      headless: true,
      // Optional override for environments where a Chromium is already present
      // (e.g. CI / containers). Leave unset to use Playwright's bundled browser.
      executablePath: process.env.PLAYWRIGHT_CHROMIUM_PATH || undefined,
      args: ["--no-sandbox", "--disable-dev-shm-usage"],
    });
    const context = await browser.newContext({
      locale: "en-US",
      userAgent:
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36",
      viewport: { width: 1280, height: 900 },
    });
    const page = await context.newPage();

    for (const niche of niches) {
      if (signal?.aborted) break;
      const query = `${niche} in ${location}`.trim();

      onStatus(`Searching Google Maps for "${query}"…`);
      await page.goto(`${MAPS_SEARCH}${encodeURIComponent(query)}?hl=en`, {
        waitUntil: "domcontentloaded",
        timeout: 45000,
      });
      await acceptConsent(page);

      // Wait for the results feed. If a single result loaded straight to a place
      // panel, fall back to scraping just that one.
      const hasFeed = await page
        .locator('div[role="feed"]')
        .waitFor({ timeout: 20000 })
        .then(() => true)
        .catch(() => false);

      const placeUrls = hasFeed
        ? await collectPlaceLinks(page, limit, onStatus)
        : [page.url()];

      onStatus(`Opening ${placeUrls.length} "${niche}" listings…`);

      for (const url of placeUrls) {
        if (signal?.aborted) break;
        const id = placeIdFromUrl(url);
        if (seenIds.has(id)) continue;
        try {
          await page.goto(url, { waitUntil: "domcontentloaded", timeout: 30000 });
          const detail = await extractDetail(page);
          if (!detail.name) continue;
          seenIds.add(id);

          const business: Business = {
            id,
            mapsUrl: url,
            niche,
            ...detail,
            emails: [],
            whatsapp: [],
            sitePhones: [],
          };

          if (enrich && business.website) {
            onStatus(`Enriching ${business.name}…`);
            const e = await enrichFromWebsite(business.website);
            business.emails = e.emails;
            business.whatsapp = e.whatsapp;
            business.sitePhones = e.sitePhones;
          }

          count += 1;
          await onBusiness(business);
          // Be polite — small delay between listings.
          await sleep(400);
        } catch {
          // Skip a single bad listing without killing the whole run.
          continue;
        }
      }
    }

    onStatus(`Done. Collected ${count} leads.`);
    return count;
  } finally {
    await browser?.close().catch(() => {});
  }
}
