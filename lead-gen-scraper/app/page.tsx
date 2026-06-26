"use client";

import { useRef, useState } from "react";
import type { Business, StreamEvent } from "@/lib/types";
import { exportToExcel, exportToVcf } from "@/lib/export";
import LeadsTable from "@/components/LeadsTable";

export default function Home() {
  const [niche, setNiche] = useState("");
  const [location, setLocation] = useState("");
  const [limit, setLimit] = useState(30);
  const [enrich, setEnrich] = useState(true);

  const [leads, setLeads] = useState<Business[]>([]);
  const [status, setStatus] = useState("");
  const [running, setRunning] = useState(false);
  const [error, setError] = useState("");
  const abortRef = useRef<AbortController | null>(null);

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

      if (!res.ok || !res.body) {
        throw new Error(await res.text().catch(() => "Request failed"));
      }

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
      <header className="mb-6">
        <h1 className="text-2xl font-bold text-slate-900">
          Lead Gen <span className="text-brand-dark">Scraper</span>
        </h1>
        <p className="mt-1 text-sm text-slate-500">
          Find businesses on Google Maps by niche &amp; location, then export to Excel or WhatsApp. Free — runs in your browser via a headless Chromium.
        </p>
      </header>

      <form onSubmit={run} className="mb-4 rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
        <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-4">
          <label className="flex flex-col gap-1">
            <span className="text-xs font-medium text-slate-600">Niche / business type</span>
            <input
              className="rounded-md border border-slate-300 px-3 py-2 text-sm outline-none focus:border-brand"
              placeholder="e.g. web development, dentists, gyms"
              value={niche}
              onChange={(e) => setNiche(e.target.value)}
              required
            />
          </label>
          <label className="flex flex-col gap-1">
            <span className="text-xs font-medium text-slate-600">Area / city / country</span>
            <input
              className="rounded-md border border-slate-300 px-3 py-2 text-sm outline-none focus:border-brand"
              placeholder="e.g. Dubai, London, India"
              value={location}
              onChange={(e) => setLocation(e.target.value)}
              required
            />
          </label>
          <label className="flex flex-col gap-1">
            <span className="text-xs font-medium text-slate-600">Max results</span>
            <input
              type="number"
              min={1}
              max={200}
              className="rounded-md border border-slate-300 px-3 py-2 text-sm outline-none focus:border-brand"
              value={limit}
              onChange={(e) => setLimit(parseInt(e.target.value, 10) || 1)}
            />
          </label>
          <div className="flex items-end gap-2">
            {!running ? (
              <button
                type="submit"
                className="w-full rounded-md bg-brand-dark px-4 py-2 text-sm font-semibold text-white hover:opacity-90"
              >
                Find leads
              </button>
            ) : (
              <button
                type="button"
                onClick={stop}
                className="w-full rounded-md bg-rose-600 px-4 py-2 text-sm font-semibold text-white hover:opacity-90"
              >
                Stop
              </button>
            )}
          </div>
        </div>

        <label className="mt-3 flex items-center gap-2 text-xs text-slate-600">
          <input type="checkbox" checked={enrich} onChange={(e) => setEnrich(e.target.checked)} />
          Visit each website to find email &amp; WhatsApp (slower, but richer data)
        </label>
      </form>

      <div className="mb-4 flex flex-wrap items-center gap-3">
        <button
          onClick={() => exportToExcel(leads, `leads-${slug || "export"}.xlsx`)}
          disabled={leads.length === 0}
          className="rounded-md border border-slate-300 bg-white px-4 py-2 text-sm font-medium text-slate-700 hover:bg-slate-50 disabled:opacity-40"
        >
          ⬇ Export Excel ({leads.length})
        </button>
        <button
          onClick={() => {
            const n = exportToVcf(leads, `leads-${slug || "export"}.vcf`);
            setStatus(`${n} contacts exported to .vcf — import it into your phone, then they appear in WhatsApp.`);
          }}
          disabled={leads.length === 0}
          className="rounded-md bg-brand px-4 py-2 text-sm font-semibold text-white hover:bg-brand-dark disabled:opacity-40"
        >
          ⬇ Export to WhatsApp (.vcf)
        </button>

        {(running || status) && (
          <span className="text-sm text-slate-500">
            {running && (
              <span className="mr-2 inline-block h-3 w-3 animate-spin rounded-full border-2 border-slate-300 border-t-brand-dark align-middle" />
            )}
            {status}
          </span>
        )}
      </div>

      {error && (
        <div className="mb-4 rounded-md border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-700">
          {error}
        </div>
      )}

      <p className="mb-2 text-xs text-slate-400">
        Note: Google Maps lists the <em>business</em> phone/website. Emails &amp; WhatsApp numbers are scraped from the
        business website where available. True decision-maker direct lines aren&apos;t available for free and need a paid
        data source (Apollo, LinkedIn, etc.).
      </p>

      <LeadsTable leads={leads} message={running ? "Scraping…" : status} />
    </main>
  );
}
