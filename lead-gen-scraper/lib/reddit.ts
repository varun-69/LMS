import type { IntentPost } from "./types";

// Phrases that signal someone is actively looking to hire / buy a service.
const INTENT_PHRASES = [
  "looking for",
  "need a",
  "need an",
  "recommend a",
  "recommendations for",
  "anyone know a",
  "hire a",
  "where can i find",
  "help with",
];

/**
 * Search Reddit for recent buying-intent posts about a service.
 * Uses Reddit's free public JSON search endpoint — no API key, no login.
 * `t` limits the time window: "day" (last 24h), "week", "month".
 */
export async function searchRedditIntent(
  service: string,
  timeframe: "day" | "week" | "month" = "day",
  limit = 40,
): Promise<IntentPost[]> {
  // Build a query like:  ("looking for" OR "need a" OR …) web development
  const phraseGroup = INTENT_PHRASES.map((p) => `"${p}"`).join(" OR ");
  const q = `(${phraseGroup}) ${service}`;

  const url =
    `https://www.reddit.com/search.json?` +
    new URLSearchParams({
      q,
      sort: "new",
      t: timeframe,
      limit: String(Math.min(limit, 100)),
      type: "link",
    }).toString();

  const res = await fetch(url, {
    headers: {
      // Reddit blocks requests without a descriptive UA.
      "User-Agent": "lead-gen-scraper/1.0 (intent radar)",
      Accept: "application/json",
    },
    // Reddit data is fine to cache briefly.
    cache: "no-store",
  });

  if (!res.ok) {
    throw new Error(`Reddit returned ${res.status}. It may be rate-limiting — try again shortly.`);
  }

  const json: any = await res.json();
  const children: any[] = json?.data?.children || [];

  return children
    .map((c) => c?.data)
    .filter(Boolean)
    .map((d: any): IntentPost => {
      const selftext = String(d.selftext || "").replace(/\s+/g, " ").trim();
      return {
        id: String(d.id),
        source: "reddit",
        title: String(d.title || "").trim(),
        snippet: selftext.slice(0, 280),
        author: String(d.author || "unknown"),
        channel: `r/${d.subreddit}`,
        url: `https://www.reddit.com${d.permalink}`,
        createdUtc: Number(d.created_utc) || 0,
      };
    })
    .filter((p) => p.title.length > 0);
}
