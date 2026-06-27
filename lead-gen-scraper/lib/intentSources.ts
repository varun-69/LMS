import type { IntentPost } from "./types";
import { searchRedditIntent } from "./reddit";

type Timeframe = "day" | "week" | "month";

const INTENT_WORDS = [
  "looking for",
  "need a",
  "need an",
  "recommend",
  "recommendation",
  "anyone know",
  "hire",
  "help with",
  "suggestions for",
  "where can i find",
];

function cutoffSeconds(timeframe: Timeframe): number {
  const days = timeframe === "day" ? 1 : timeframe === "week" ? 7 : 30;
  return Math.floor(Date.now() / 1000) - days * 86400;
}

function hasIntent(text: string): boolean {
  const t = text.toLowerCase();
  return INTENT_WORDS.some((w) => t.includes(w));
}

function hostOf(url: string): string {
  try {
    return new URL(url).hostname.replace(/^www\./, "");
  } catch {
    return "web";
  }
}

async function fetchJson(url: string, init: RequestInit, timeoutMs: number): Promise<any | null> {
  const controller = new AbortController();
  const t = setTimeout(() => controller.abort(), timeoutMs);
  try {
    const res = await fetch(url, { ...init, signal: controller.signal });
    if (!res.ok) return null;
    return await res.json();
  } catch {
    return null;
  } finally {
    clearTimeout(t);
  }
}

/** Hacker News via the free Algolia search API — no key required. */
export async function searchHackerNews(service: string, timeframe: Timeframe): Promise<IntentPost[]> {
  const since = cutoffSeconds(timeframe);
  const url =
    `https://hn.algolia.com/api/v1/search_by_date?` +
    new URLSearchParams({
      query: service,
      tags: "(story,comment,ask_hn)",
      numericFilters: `created_at_i>${since}`,
      hitsPerPage: "40",
    }).toString();

  const json = await fetchJson(url, { headers: { Accept: "application/json" } }, 8000);
  const hits: any[] = json?.hits || [];

  return hits
    .map((h): IntentPost | null => {
      const title = String(h.title || h.story_title || "").trim();
      const body = String(h.comment_text || h.story_text || "").replace(/<[^>]+>/g, " ").trim();
      const text = `${title} ${body}`;
      if (!hasIntent(text)) return null;
      return {
        id: `hn_${h.objectID}`,
        source: "hackernews",
        title: title || body.slice(0, 90),
        snippet: body.slice(0, 280),
        author: String(h.author || "unknown"),
        channel: "Hacker News",
        url: `https://news.ycombinator.com/item?id=${h.objectID}`,
        createdUtc: Number(h.created_at_i) || 0,
      };
    })
    .filter((p): p is IntentPost => p !== null);
}

/** Web-wide search via Jina Search (s.jina.ai) — free, no key (key raises limits). */
export async function searchWebIntent(service: string, location: string): Promise<IntentPost[]> {
  const q = `("looking for" OR "need a" OR "recommend" OR "anyone know") ${service} ${location}`.trim();
  const headers: Record<string, string> = { Accept: "application/json", "X-Respond-With": "no-content" };
  if (process.env.JINA_API_KEY) headers.Authorization = `Bearer ${process.env.JINA_API_KEY}`;

  const json = await fetchJson(`https://s.jina.ai/${encodeURIComponent(q)}`, { headers }, 12000);
  const data: any[] = json?.data || [];

  return data.slice(0, 20).map((d): IntentPost => ({
    id: `web_${hostOf(d.url)}_${(d.title || "").slice(0, 24)}`,
    source: "web",
    title: String(d.title || "").trim() || hostOf(d.url),
    snippet: String(d.description || d.content || "").replace(/\s+/g, " ").slice(0, 280),
    author: "",
    channel: hostOf(d.url),
    url: String(d.url || ""),
    createdUtc: 0,
  }));
}

/** Exa semantic search — optional, only runs if EXA_API_KEY is set. Best quality. */
export async function searchExaIntent(service: string, timeframe: Timeframe): Promise<IntentPost[]> {
  if (!process.env.EXA_API_KEY) return [];
  const startPublishedDate = new Date(cutoffSeconds(timeframe) * 1000).toISOString();
  const query = `Someone looking for / needing / asking for help with ${service}`;

  const json = await fetchJson(
    "https://api.exa.ai/search",
    {
      method: "POST",
      headers: { "Content-Type": "application/json", "x-api-key": process.env.EXA_API_KEY },
      body: JSON.stringify({ query, type: "auto", numResults: 20, startPublishedDate }),
    },
    12000,
  );
  const results: any[] = json?.results || [];

  return results.map((r): IntentPost => ({
    id: `exa_${r.id || hostOf(r.url)}`,
    source: "exa",
    title: String(r.title || "").trim() || hostOf(r.url),
    snippet: String(r.text || r.summary || "").replace(/\s+/g, " ").slice(0, 280),
    author: String(r.author || ""),
    channel: hostOf(r.url),
    url: String(r.url || ""),
    createdUtc: r.publishedDate ? Math.floor(new Date(r.publishedDate).getTime() / 1000) : 0,
  }));
}

export interface IntentResult {
  posts: IntentPost[];
  warnings: string[];
  /** Per-source counts for the UI summary. */
  counts: Record<string, number>;
}

/**
 * Run every free, read-only intent source in parallel and merge the results.
 * One slow/failed source never blocks the others.
 */
export async function gatherIntent(
  service: string,
  location: string,
  timeframe: Timeframe,
): Promise<IntentResult> {
  const tasks: { name: string; run: Promise<IntentPost[]> }[] = [
    { name: "Reddit", run: searchRedditIntent(service, timeframe) },
    { name: "Hacker News", run: searchHackerNews(service, timeframe) },
    { name: "Web", run: searchWebIntent(service, location) },
    { name: "Exa", run: searchExaIntent(service, timeframe) },
  ];

  const settled = await Promise.allSettled(tasks.map((t) => t.run));

  const warnings: string[] = [];
  const merged: IntentPost[] = [];
  const counts: Record<string, number> = {};

  settled.forEach((s, i) => {
    const name = tasks[i].name;
    if (s.status === "fulfilled") {
      counts[name] = s.value.length;
      merged.push(...s.value);
    } else {
      warnings.push(`${name} unavailable`);
    }
  });

  // Dedupe by URL, then sort newest-first (undated results sink to the bottom).
  const seen = new Set<string>();
  const posts = merged
    .filter((p) => {
      const key = p.url || p.id;
      if (seen.has(key)) return false;
      seen.add(key);
      return true;
    })
    .sort((a, b) => b.createdUtc - a.createdUtc)
    .slice(0, 80);

  return { posts, warnings, counts };
}
