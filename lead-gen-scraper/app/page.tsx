"use client";

import { useMemo, useRef, useState } from "react";
import type { Business, StreamEvent } from "@/lib/types";
import { bestWhatsAppNumber, exportToExcel, exportToVcf } from "@/lib/export";
import LeadsTable from "@/components/LeadsTable";
import IntentRadar from "@/components/IntentRadar";
import DraftDialog, { type DraftTarget } from "@/components/DraftDialog";

type Tab = "maps" | "intent";
type WebsiteFilter = "all" | "no" | "yes";

export default function Home() {
  const [tab, setTab] = useState<Tab>("maps");

  // Shared inputs
  const [niche, setNiche] = useState("");
  const [location, setLocation] = useState("");
  const [service, setService] = useState("");
  const [bookingLink, setBookingLink] = useState("");

  // Maps inputs
  const [limit, setLimit] = useState(30);
  const [enrich, setEnrich] = useState(true);

  // Filters
  const [websiteFilter, setWebsiteFilter] = useState<WebsiteFilter>("all");
  const [minRating, setMinRating] = useState(0);
  const [hasEmail, setHasEmail] = useState(false);
  const [hasWhatsApp, setHasWhatsApp] = useState(false);

  // Run state
  const [leads, setLeads] = useState<Business[]>([]);
  const [status, setStatus] = useState("");
  const [running, setRunning] = useState(false);
  const [error, setError] = useState("");
  const abortRef = useRef<AbortController | null>(null);

  // AI draft dialog
  const [draftTarget, setDraftTarget] = useState<DraftTarget | null>(null);
  const effectiveService = service.trim() || niche.trim();

  const filtered = useMemo(() => {
    return leads.filter((b) => {
      if (websiteFilter === "no" && b.website) return false;
      if (websiteFilter === "yes" && !b.website) return false;
      if (minRating > 0 && (parseFloat(b.rating) || 0) < minRating) return false;
      if (hasEmail && b.emails.length === 0) return false;
      if (hasWhatsApp && !bestWhatsAppNumber(b)) return false;
      return true;
    });
  }, [leads, websiteFilter, minRating, hasEmail, hasWhatsApp]);

  async function run(e: React.FormEvent) {
    e.preventDefault();
    if (!niche.trim() || !location.trim() || running) return;

    setLeads([]);
    setError("");
    setRunning(true);
    setStatus("Starting…");

    const controller = new AbortController();
    abortRef.current = controller;

    try {
      const res = await fetch("/api/scrape", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ niche, location, limit, enrich }),
        signal: controller.signal,
      });
      if (!res.ok || !res.body) throw new Error(await res.text().catch(() => "Request failed"));

      const reader = res.body.getReader();
      const decoder = new TextDecoder();
      let buffer = "";

      for (;;) {
        const { done, value } = await reader.read();
        if (done) break;
        buffer += decoder.decode(value, { stream: true });
        let nl: number;
        while ((nl = buffer.indexOf("\n")) >= 0) {
          const line = buffer.slice(0, nl).trim();
          buffer = buffer.slice(nl + 1);
          if (!line) continue;
          const evt = JSON.parse(line) as StreamEvent;
          if (evt.type === "status") setStatus(evt.message);
          else if (evt.type === "lead") setLeads((prev) => [...prev, evt.data]);
          else if (evt.type === "error") setError(evt.message);
          else if (evt.type === "done") setStatus(`Finished — ${evt.count} leads collected.`);
        }
      }
    } catch (err: any) {
      if (err?.name !== "AbortError") setError(err?.message || "Something went wrong");
    } finally {
      setRunning(false);
      abortRef.current = null;
    }
  }

  function stop() {
    abortRef.current?.abort();
    setRunning(false);
    setStatus("Stopped.");
  }

  const slug = `${niche}-${location}`.toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/^-|-$/g, "");

  return (
    <main className="mx-auto max-w-6xl px-4 py-8">
      <header className="mb-5">
        <h1 className="text-2xl font-bold text-slate-900">
          Lead Gen <span className="text-brand-dark">Scraper</span>
        </h1>
        <p className="mt-1 text-sm text-slate-500">
          Google Maps leads + a live “who needs my service right now” radar, with AI-written outreach. Free — runs locally.
        </p>
      </header>

      {/* Shared inputs */}
      <div className="mb-4 grid grid-cols-1 gap-3 rounded-xl border border-slate-200 bg-white p-4 shadow-sm sm:grid-cols-2 lg:grid-cols-4">
        <label className="flex flex-col gap-1">
          <span className="text-xs font-medium text-slate-600">Niche(s) — comma separated</span>
          <input
            className="rounded-md border border-slate-300 px-3 py-2 text-sm outline-none focus:border-brand"
            placeholder="web development, SEO, digital marketing"
            value={niche}
            onChange={(e) => setNiche(e.target.value)}
          />
        </label>
        <label className="flex flex-col gap-1">
          <span className="text-xs font-medium text-slate-600">Area / city / country</span>
          <input
            className="rounded-md border border-slate-300 px-3 py-2 text-sm outline-none focus:border-brand"
            placeholder="Dubai, London, India"
            value={location}
            onChange={(e) => setLocation(e.target.value)}
          />
        </label>
        <label className="flex flex-col gap-1">
          <span className="text-xs font-medium text-slate-600">What you offer (for AI &amp; intent)</span>
          <input
            className="rounded-md border border-slate-300 px-3 py-2 text-sm outline-none focus:border-brand"
            placeholder={niche ? `defaults to “${niche}”` : "web design for restaurants"}
            value={service}
            onChange={(e) => setService(e.target.value)}
          />
        </label>
        <label className="flex flex-col gap-1">
          <span className="text-xs font-medium text-slate-600">Booking link (optional)</span>
          <input
            className="rounded-md border border-slate-300 px-3 py-2 text-sm outline-none focus:border-brand"
            placeholder="https://cal.com/you/15min"
            value={bookingLink}
            onChange={(e) => setBookingLink(e.target.value)}
          />
        </label>
      </div>

      {/* Tabs */}
      <div className="mb-4 flex gap-1 border-b border-slate-200">
        {([["maps", "🗺️ Maps Leads"], ["intent", "📡 Intent Radar"]] as [Tab, string][]).map(([id, lbl]) => (
          <button
            key={id}
            onClick={() => setTab(id)}
            className={`-mb-px border-b-2 px-4 py-2 text-sm font-medium ${
              tab === id ? "border-brand-dark text-brand-dark" : "border-transparent text-slate-500 hover:text-slate-800"
            }`}
          >
            {lbl}
          </button>
        ))}
      </div>

      {tab === "maps" && (
        <>
          <form onSubmit={run} className="mb-4 flex flex-wrap items-end gap-3">
            <label className="flex flex-col gap-1">
              <span className="text-xs font-medium text-slate-600">Max results / niche</span>
              <input
                type="number"
                min={1}
                max={200}
                className="w-28 rounded-md border border-slate-300 px-3 py-2 text-sm outline-none focus:border-brand"
                value={limit}
                onChange={(e) => setLimit(parseInt(e.target.value, 10) || 1)}
              />
            </label>
            <label className="flex items-center gap-2 pb-2 text-xs text-slate-600">
              <input type="checkbox" checked={enrich} onChange={(e) => setEnrich(e.target.checked)} />
              Find email &amp; WhatsApp from websites
            </label>
            {!running ? (
              <button type="submit" className="rounded-md bg-brand-dark px-4 py-2 text-sm font-semibold text-white hover:opacity-90">
                Find leads
              </button>
            ) : (
              <button type="button" onClick={stop} className="rounded-md bg-rose-600 px-4 py-2 text-sm font-semibold text-white hover:opacity-90">
                Stop
              </button>
            )}
          </form>

          {/* Filters */}
          <div className="mb-3 flex flex-wrap items-center gap-3 rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm">
            <span className="text-xs font-medium text-slate-500">Filter:</span>
            <select value={websiteFilter} onChange={(e) => setWebsiteFilter(e.target.value as WebsiteFilter)} className="rounded border border-slate-300 px-2 py-1 text-xs">
              <option value="all">All websites</option>
              <option value="no">No website only</option>
              <option value="yes">Has website only</option>
            </select>
            <label className="flex items-center gap-1 text-xs text-slate-600">
              Min rating
              <select value={minRating} onChange={(e) => setMinRating(parseFloat(e.target.value))} className="rounded border border-slate-300 px-2 py-1 text-xs">
                {[0, 3, 3.5, 4, 4.5].map((r) => (
                  <option key={r} value={r}>{r === 0 ? "any" : `${r}+`}</option>
                ))}
              </select>
            </label>
            <label className="flex items-center gap-1 text-xs text-slate-600">
              <input type="checkbox" checked={hasEmail} onChange={(e) => setHasEmail(e.target.checked)} /> has email
            </label>
            <label className="flex items-center gap-1 text-xs text-slate-600">
              <input type="checkbox" checked={hasWhatsApp} onChange={(e) => setHasWhatsApp(e.target.checked)} /> has WhatsApp
            </label>
            <span className="ml-auto text-xs text-slate-400">
              Showing {filtered.length} of {leads.length}
            </span>
          </div>

          {/* Export + status */}
          <div className="mb-3 flex flex-wrap items-center gap-3">
            <button
              onClick={() => exportToExcel(filtered, `leads-${slug || "export"}.xlsx`)}
              disabled={filtered.length === 0}
              className="rounded-md border border-slate-300 bg-white px-4 py-2 text-sm font-medium text-slate-700 hover:bg-slate-50 disabled:opacity-40"
            >
              ⬇ Export Excel ({filtered.length})
            </button>
            <button
              onClick={() => {
                const n = exportToVcf(filtered, `leads-${slug || "export"}.vcf`);
                setStatus(`${n} contacts exported to .vcf — import into your phone, then they appear in WhatsApp.`);
              }}
              disabled={filtered.length === 0}
              className="rounded-md bg-brand px-4 py-2 text-sm font-semibold text-white hover:bg-brand-dark disabled:opacity-40"
            >
              ⬇ Export to WhatsApp (.vcf)
            </button>
            {(running || status) && (
              <span className="text-sm text-slate-500">
                {running && <span className="mr-2 inline-block h-3 w-3 animate-spin rounded-full border-2 border-slate-300 border-t-brand-dark align-middle" />}
                {status}
              </span>
            )}
          </div>

          {error && (
            <div className="mb-4 rounded-md border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-700">{error}</div>
          )}

          <p className="mb-2 text-xs text-slate-400">
            Google Maps lists the <em>business</em> phone/website. Emails &amp; WhatsApp are scraped from business sites where available. True decision-maker direct lines need a paid source (Apollo, LinkedIn) — not available for free.
          </p>

          <LeadsTable leads={filtered} message={running ? "Scraping…" : status} onDraft={setDraftTarget} />
        </>
      )}

      {tab === "intent" && (
        <IntentRadar service={effectiveService} location={location} onDraft={setDraftTarget} />
      )}

      {draftTarget && (
        <DraftDialog target={draftTarget} service={effectiveService} bookingLink={bookingLink} onClose={() => setDraftTarget(null)} />
      )}
    </main>
  );
}
