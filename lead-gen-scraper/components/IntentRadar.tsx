"use client";

import { useState } from "react";
import type { IntentLink, IntentPost } from "@/lib/types";
import type { DraftTarget } from "./DraftDialog";

function timeAgo(epoch: number): string {
  if (!epoch) return "";
  const secs = Math.max(1, Math.floor(Date.now() / 1000 - epoch));
  if (secs < 3600) return `${Math.floor(secs / 60)}m ago`;
  if (secs < 86400) return `${Math.floor(secs / 3600)}h ago`;
  return `${Math.floor(secs / 86400)}d ago`;
}

const SOURCE_STYLE: Record<string, { label: string; cls: string }> = {
  reddit: { label: "Reddit", cls: "bg-orange-100 text-orange-700" },
  hackernews: { label: "HN", cls: "bg-amber-100 text-amber-800" },
  web: { label: "Web", cls: "bg-sky-100 text-sky-700" },
  exa: { label: "Exa", cls: "bg-violet-100 text-violet-700" },
};

function SourceChip({ source }: { source: string }) {
  const s = SOURCE_STYLE[source] || { label: source, cls: "bg-slate-100 text-slate-600" };
  return <span className={`rounded px-1.5 py-0.5 text-[10px] font-medium ${s.cls}`}>{s.label}</span>;
}

export default function IntentRadar({
  service,
  location,
  onDraft,
}: {
  service: string;
  location: string;
  onDraft: (t: DraftTarget) => void;
}) {
  const [timeframe, setTimeframe] = useState<"day" | "week" | "month">("day");
  const [loading, setLoading] = useState(false);
  const [posts, setPosts] = useState<IntentPost[]>([]);
  const [links, setLinks] = useState<IntentLink[]>([]);
  const [counts, setCounts] = useState<Record<string, number>>({});
  const [warning, setWarning] = useState("");
  const [ran, setRan] = useState(false);

  async function run() {
    if (!service.trim()) {
      setWarning("Enter what you offer (the “niche” field) up top first.");
      return;
    }
    setLoading(true);
    setWarning("");
    try {
      const res = await fetch("/api/intent", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ service, location, timeframe }),
      });
      const json = await res.json();
      setPosts(json.posts || []);
      setLinks(json.links || []);
      setCounts(json.counts || {});
      if (json.warning) setWarning(json.warning);
    } catch (e: any) {
      setWarning(e?.message || "Search failed");
    } finally {
      setLoading(false);
      setRan(true);
    }
  }

  return (
    <div className="space-y-5">
      <div className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
        <div className="flex flex-wrap items-end gap-3">
          <div className="text-sm text-slate-600">
            Find people <span className="font-medium">asking for “{service || "your service"}”</span>
            {location ? ` near ${location}` : ""} in the last…
          </div>
          <select
            value={timeframe}
            onChange={(e) => setTimeframe(e.target.value as any)}
            className="rounded-md border border-slate-300 px-2 py-1.5 text-sm"
          >
            <option value="day">24 hours</option>
            <option value="week">7 days</option>
            <option value="month">30 days</option>
          </select>
          <button
            onClick={run}
            disabled={loading}
            className="rounded-md bg-brand-dark px-4 py-2 text-sm font-semibold text-white hover:opacity-90 disabled:opacity-50"
          >
            {loading ? "Scanning…" : "Scan intent"}
          </button>
        </div>
        {warning && <p className="mt-2 text-xs text-amber-600">{warning}</p>}
      </div>

      {/* Multi-source intent feed (Reddit + HN + Web + Exa) */}
      <div>
        <div className="mb-2 flex flex-wrap items-center gap-2">
          <h3 className="text-sm font-semibold text-slate-700">
            Live buying-intent posts {posts.length ? `(${posts.length})` : ""}
          </h3>
          {Object.entries(counts)
            .filter(([, n]) => n > 0)
            .map(([name, n]) => (
              <span key={name} className="rounded bg-slate-100 px-1.5 py-0.5 text-[10px] text-slate-500">
                {name}: {n}
              </span>
            ))}
        </div>
        <div className="space-y-2">
          {posts.map((p) => (
            <div key={p.id} className="rounded-lg border border-slate-200 bg-white p-3 shadow-sm">
              <div className="flex items-start justify-between gap-3">
                <div className="min-w-0">
                  <div className="flex items-center gap-2">
                    <SourceChip source={p.source} />
                    <a href={p.url} target="_blank" rel="noreferrer" className="font-medium text-slate-900 hover:underline">
                      {p.title}
                    </a>
                  </div>
                  {p.snippet && <p className="mt-0.5 line-clamp-2 text-xs text-slate-500">{p.snippet}</p>}
                  <p className="mt-1 text-xs text-slate-400">
                    {p.channel}
                    {p.author ? ` · ${p.source === "reddit" ? "u/" : ""}${p.author}` : ""}
                    {p.createdUtc ? ` · ${timeAgo(p.createdUtc)}` : ""}
                  </p>
                </div>
                <button
                  onClick={() =>
                    onDraft({
                      targetName: p.author ? `${p.author} on ${p.channel}` : p.channel,
                      context: `They posted: "${p.title}". ${p.snippet}`.trim(),
                      kind: "intent",
                      openUrl: p.url,
                    })
                  }
                  className="shrink-0 rounded-md bg-brand/10 px-3 py-1.5 text-xs font-medium text-brand-dark hover:bg-brand/20"
                >
                  Draft reply
                </button>
              </div>
            </div>
          ))}
          {ran && posts.length === 0 && (
            <p className="rounded-lg border border-dashed border-slate-200 bg-white px-3 py-6 text-center text-sm text-slate-400">
              Nothing in this window across Reddit, Hacker News or the web. Try a wider timeframe or the search links below.
            </p>
          )}
        </div>
      </div>

      {/* One-click intent searches on platforms that can't be scraped for free */}
      {links.length > 0 && (
        <div>
          <h3 className="mb-1 text-sm font-semibold text-slate-700">Open intent searches on other platforms</h3>
          <p className="mb-2 text-xs text-slate-400">
            These open each platform’s own search (you’re already logged in), pre-filtered to your service + “looking for / need / recommend” + recent. Free and ToS-safe — no scraping.
          </p>
          <div className="flex flex-wrap gap-2">
            {links.map((l) => (
              <a
                key={l.platform + l.label}
                href={l.url}
                target="_blank"
                rel="noreferrer"
                className="rounded-md border border-slate-300 bg-white px-3 py-2 text-sm text-slate-700 hover:bg-slate-50"
              >
                <span className="font-medium">{l.platform}</span>
                <span className="text-slate-400"> · {l.label} ↗</span>
              </a>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
