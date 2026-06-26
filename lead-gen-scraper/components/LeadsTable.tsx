"use client";

import type { Business } from "@/lib/types";
import { bestWhatsAppNumber, whatsAppLink } from "@/lib/export";
import type { DraftTarget } from "./DraftDialog";

function Stars({ rating }: { rating: string }) {
  if (!rating) return <span className="text-slate-400">—</span>;
  return <span className="whitespace-nowrap text-amber-600">★ {rating}</span>;
}

export default function LeadsTable({
  leads,
  message,
  onDraft,
}: {
  leads: Business[];
  message: string;
  onDraft: (t: DraftTarget) => void;
}) {
  return (
    <div className="overflow-x-auto rounded-xl border border-slate-200 bg-white shadow-sm">
      <table className="w-full border-collapse text-sm">
        <thead className="sticky top-0 bg-slate-100 text-left text-slate-600">
          <tr>
            <th className="px-3 py-2 font-medium">#</th>
            <th className="px-3 py-2 font-medium">Business</th>
            <th className="px-3 py-2 font-medium">Rating</th>
            <th className="px-3 py-2 font-medium">Phone</th>
            <th className="px-3 py-2 font-medium">WhatsApp</th>
            <th className="px-3 py-2 font-medium">Email</th>
            <th className="px-3 py-2 font-medium">Website</th>
            <th className="px-3 py-2 font-medium">Outreach</th>
          </tr>
        </thead>
        <tbody>
          {leads.map((b, i) => {
            const wa = bestWhatsAppNumber(b);
            return (
              <tr key={b.id + i} className="border-t border-slate-100 align-top hover:bg-slate-50">
                <td className="px-3 py-2 text-slate-400">{i + 1}</td>
                <td className="px-3 py-2">
                  <div className="font-medium text-slate-900">{b.name}</div>
                  <div className="text-xs text-slate-500">
                    {b.category}
                    {b.niche && <span className="ml-1 rounded bg-slate-100 px-1.5 py-0.5 text-[10px] text-slate-500">{b.niche}</span>}
                  </div>
                </td>
                <td className="px-3 py-2">
                  <Stars rating={b.rating} />
                  <div className="text-xs text-slate-400">{b.reviews ? `${b.reviews} reviews` : ""}</div>
                </td>
                <td className="px-3 py-2 whitespace-nowrap">{b.phone || "—"}</td>
                <td className="px-3 py-2 whitespace-nowrap">
                  {wa ? (
                    <a
                      href={whatsAppLink(wa, "")}
                      target="_blank"
                      rel="noreferrer"
                      className="inline-flex items-center gap-1 rounded-md bg-brand/10 px-2 py-1 text-xs font-medium text-brand-dark hover:bg-brand/20"
                    >
                      Chat ↗
                    </a>
                  ) : (
                    <span className="text-slate-400">—</span>
                  )}
                </td>
                <td className="px-3 py-2">
                  {b.emails.length ? (
                    <a className="text-blue-600 hover:underline" href={`mailto:${b.emails[0]}`}>
                      {b.emails[0]}
                    </a>
                  ) : (
                    <span className="text-slate-400">—</span>
                  )}
                </td>
                <td className="px-3 py-2 max-w-[14rem] truncate">
                  {b.website ? (
                    <a className="text-blue-600 hover:underline" href={b.website} target="_blank" rel="noreferrer">
                      {b.website.replace(/^https?:\/\//, "").replace(/\/$/, "")}
                    </a>
                  ) : (
                    <span className="rounded bg-amber-100 px-1.5 py-0.5 text-[11px] font-medium text-amber-700">No website</span>
                  )}
                </td>
                <td className="px-3 py-2">
                  <button
                    onClick={() =>
                      onDraft({
                        targetName: b.name,
                        context: [
                          `Category: ${b.category || "n/a"}.`,
                          b.rating ? `Rating: ${b.rating} (${b.reviews || "?"} reviews).` : "",
                          b.website ? `Website: ${b.website}.` : "They have NO website.",
                          `Located at: ${b.address || "n/a"}.`,
                        ]
                          .filter(Boolean)
                          .join(" "),
                        kind: "lead",
                        whatsappNumber: wa,
                        email: b.emails[0] || null,
                        openUrl: b.mapsUrl,
                      })
                    }
                    className="rounded-md bg-brand-dark px-2.5 py-1 text-xs font-medium text-white hover:opacity-90"
                  >
                    ✨ Draft
                  </button>
                </td>
              </tr>
            );
          })}
          {leads.length === 0 && (
            <tr>
              <td colSpan={8} className="px-3 py-10 text-center text-slate-400">
                {message || "No leads yet. Run a search above."}
              </td>
            </tr>
          )}
        </tbody>
      </table>
    </div>
  );
}
