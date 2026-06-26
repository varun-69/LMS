"use client";

import { useEffect, useState } from "react";
import type { DraftRequest, DraftResponse } from "@/lib/types";

export interface DraftTarget {
  targetName: string;
  context: string;
  kind: "lead" | "intent";
  /** A wa.me-able number, if known, for the "Send WhatsApp" button. */
  whatsappNumber?: string | null;
  /** A mailto address, if known. */
  email?: string | null;
  /** External link to open the conversation (e.g. the Reddit/LinkedIn post). */
  openUrl?: string | null;
}

export default function DraftDialog({
  target,
  service,
  bookingLink,
  onClose,
}: {
  target: DraftTarget;
  service: string;
  bookingLink: string;
  onClose: () => void;
}) {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [draft, setDraft] = useState<DraftResponse | null>(null);

  async function generate() {
    setLoading(true);
    setError("");
    try {
      const payload: DraftRequest = {
        service,
        targetName: target.targetName,
        context: target.context,
        bookingLink: bookingLink || undefined,
        kind: target.kind,
      };
      const res = await fetch("/api/draft", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      const json = await res.json();
      if (!res.ok) throw new Error(json?.error || "Draft failed");
      setDraft(json as DraftResponse);
    } catch (e: any) {
      setError(e?.message || "Something went wrong");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    if (!service.trim()) {
      setError("Set the “What you offer” field at the top first, then try again.");
      setLoading(false);
      return;
    }
    generate();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const copy = (text: string) => navigator.clipboard?.writeText(text);

  const waHref = target.whatsappNumber
    ? `https://wa.me/${target.whatsappNumber.replace(/[^\d]/g, "")}?text=${encodeURIComponent(
        draft?.whatsapp || "",
      )}`
    : null;
  const mailHref = target.email
    ? `mailto:${target.email}?subject=${encodeURIComponent(
        draft?.emailSubject || "",
      )}&body=${encodeURIComponent(draft?.emailBody || "")}`
    : null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4" onClick={onClose}>
      <div
        className="max-h-[90vh] w-full max-w-xl overflow-y-auto rounded-xl bg-white p-5 shadow-xl"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="mb-3 flex items-start justify-between">
          <div>
            <h3 className="text-lg font-semibold text-slate-900">AI outreach draft</h3>
            <p className="text-xs text-slate-500">For: {target.targetName}</p>
          </div>
          <button onClick={onClose} className="text-slate-400 hover:text-slate-700">
            ✕
          </button>
        </div>

        {loading && (
          <div className="py-10 text-center text-sm text-slate-500">
            <span className="mr-2 inline-block h-4 w-4 animate-spin rounded-full border-2 border-slate-300 border-t-brand-dark align-middle" />
            Claude is writing a personalized message…
          </div>
        )}

        {error && (
          <div className="rounded-md border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-700">
            {error}
          </div>
        )}

        {draft && (
          <div className="space-y-4">
            <Field label="Email subject" value={draft.emailSubject} onChange={(v) => setDraft({ ...draft, emailSubject: v })} onCopy={copy} rows={1} />
            <Field label="Email body" value={draft.emailBody} onChange={(v) => setDraft({ ...draft, emailBody: v })} onCopy={copy} rows={5} />
            <Field label="WhatsApp message" value={draft.whatsapp} onChange={(v) => setDraft({ ...draft, whatsapp: v })} onCopy={copy} rows={3} />
            <Field label="DM (LinkedIn / Instagram)" value={draft.dm} onChange={(v) => setDraft({ ...draft, dm: v })} onCopy={copy} rows={3} />

            <div className="flex flex-wrap gap-2 pt-1">
              {waHref && (
                <a href={waHref} target="_blank" rel="noreferrer" className="rounded-md bg-brand px-3 py-2 text-sm font-semibold text-white hover:bg-brand-dark">
                  Send on WhatsApp
                </a>
              )}
              {mailHref && (
                <a href={mailHref} className="rounded-md border border-slate-300 px-3 py-2 text-sm font-medium text-slate-700 hover:bg-slate-50">
                  Open in email
                </a>
              )}
              {target.openUrl && (
                <a href={target.openUrl} target="_blank" rel="noreferrer" className="rounded-md border border-slate-300 px-3 py-2 text-sm font-medium text-slate-700 hover:bg-slate-50">
                  Open the post ↗
                </a>
              )}
              <button onClick={generate} className="ml-auto rounded-md px-3 py-2 text-sm text-slate-500 hover:text-slate-800">
                ↻ Regenerate
              </button>
            </div>
            <p className="text-xs text-slate-400">
              Review and edit before sending. You send it yourself — nothing is sent automatically.
            </p>
          </div>
        )}
      </div>
    </div>
  );
}

function Field({
  label,
  value,
  onChange,
  onCopy,
  rows,
}: {
  label: string;
  value: string;
  onChange: (v: string) => void;
  onCopy: (v: string) => void;
  rows: number;
}) {
  return (
    <div>
      <div className="mb-1 flex items-center justify-between">
        <span className="text-xs font-medium text-slate-600">{label}</span>
        <button onClick={() => onCopy(value)} className="text-xs text-blue-600 hover:underline">
          Copy
        </button>
      </div>
      <textarea
        value={value}
        onChange={(e) => onChange(e.target.value)}
        rows={rows}
        className="w-full resize-y rounded-md border border-slate-300 px-3 py-2 text-sm outline-none focus:border-brand"
      />
    </div>
  );
}
