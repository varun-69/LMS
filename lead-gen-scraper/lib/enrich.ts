import * as cheerio from "cheerio";

const EMAIL_RE = /[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}/g;

// Junk that turns up when regex-matching emails out of raw HTML/JS.
const EMAIL_BLOCKLIST = [
  "example.com",
  "sentry.io",
  "sentry-next.wixpress.com",
  "wixpress.com",
  "wix.com",
  "domain.com",
  "yourdomain",
  "email.com",
  "godaddy",
  "squarespace",
  ".png",
  ".jpg",
  ".jpeg",
  ".gif",
  ".svg",
  ".webp",
  ".css",
  ".js",
];

function isJunkEmail(email: string): boolean {
  const e = email.toLowerCase();
  if (EMAIL_BLOCKLIST.some((b) => e.includes(b))) return true;
  // u0040-style or obviously truncated matches
  if (e.length > 80) return true;
  return false;
}

/** Pull the digits out of a wa.me / api.whatsapp.com / web.whatsapp.com link. */
function whatsappFromHref(href: string): string | null {
  try {
    const url = new URL(href, "https://x.invalid");
    if (url.hostname.includes("wa.me")) {
      const num = url.pathname.replace(/\D/g, "");
      return num.length >= 7 ? num : null;
    }
    if (url.hostname.includes("whatsapp.com")) {
      const phone = url.searchParams.get("phone");
      if (phone) {
        const num = phone.replace(/\D/g, "");
        return num.length >= 7 ? num : null;
      }
    }
  } catch {
    /* ignore malformed urls */
  }
  return null;
}

function normalizeBase(website: string): string | null {
  try {
    const u = new URL(website);
    return `${u.protocol}//${u.host}`;
  } catch {
    return null;
  }
}

async function fetchText(url: string, timeoutMs: number): Promise<string | null> {
  const controller = new AbortController();
  const t = setTimeout(() => controller.abort(), timeoutMs);
  try {
    const res = await fetch(url, {
      signal: controller.signal,
      redirect: "follow",
      headers: {
        "User-Agent":
          "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36",
        Accept: "text/html,application/xhtml+xml",
      },
    });
    if (!res.ok) return null;
    const ct = res.headers.get("content-type") || "";
    if (!ct.includes("html") && !ct.includes("text")) return null;
    return await res.text();
  } catch {
    return null;
  } finally {
    clearTimeout(t);
  }
}

export interface EnrichResult {
  emails: string[];
  whatsapp: string[];
  sitePhones: string[];
}

/**
 * Visit a business website (home + a couple of likely contact pages) and
 * extract emails, WhatsApp numbers and any phone numbers. Best-effort and
 * fully free — it just reads public HTML. Never throws.
 */
export async function enrichFromWebsite(website: string): Promise<EnrichResult> {
  const emails = new Set<string>();
  const whatsapp = new Set<string>();
  const sitePhones = new Set<string>();

  const base = normalizeBase(website);
  if (!base) return { emails: [], whatsapp: [], sitePhones: [] };

  const candidates = [
    base,
    `${base}/contact`,
    `${base}/contact-us`,
    `${base}/about`,
    `${base}/contacto`,
  ];

  for (const url of candidates) {
    const html = await fetchText(url, 7000);
    if (!html) continue;

    let $: cheerio.CheerioAPI;
    try {
      $ = cheerio.load(html);
    } catch {
      continue;
    }

    // mailto: links — the most reliable email source.
    $('a[href^="mailto:"]').each((_, el) => {
      const raw = ($(el).attr("href") || "").replace(/^mailto:/i, "").split("?")[0].trim();
      if (raw && !isJunkEmail(raw)) emails.add(raw.toLowerCase());
    });

    // tel: links.
    $('a[href^="tel:"]').each((_, el) => {
      const raw = ($(el).attr("href") || "").replace(/^tel:/i, "").trim();
      const cleaned = raw.replace(/[^\d+]/g, "");
      if (cleaned.replace(/\D/g, "").length >= 7) sitePhones.add(cleaned);
    });

    // WhatsApp click-to-chat links.
    $('a[href*="wa.me"], a[href*="whatsapp.com"]').each((_, el) => {
      const num = whatsappFromHref($(el).attr("href") || "");
      if (num) whatsapp.add(num);
    });

    // Fallback: regex emails out of the raw HTML.
    const matches = html.match(EMAIL_RE) || [];
    for (const m of matches) {
      if (!isJunkEmail(m)) emails.add(m.toLowerCase());
    }

    // Once we have a solid email + whatsapp, stop crawling more pages.
    if (emails.size > 0 && whatsapp.size > 0) break;
  }

  return {
    emails: [...emails].slice(0, 5),
    whatsapp: [...whatsapp].slice(0, 5),
    sitePhones: [...sitePhones].slice(0, 5),
  };
}
