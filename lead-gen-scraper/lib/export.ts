import * as XLSX from "xlsx";
import type { Business } from "./types";

/** Flatten a lead into a single spreadsheet row. */
function toRow(b: Business) {
  return {
    Name: b.name,
    Category: b.category,
    Rating: b.rating,
    Reviews: b.reviews,
    Phone: b.phone,
    WhatsApp: b.whatsapp.join(", "),
    Email: b.emails.join(", "),
    "Other phones": b.sitePhones.join(", "),
    Website: b.website,
    Address: b.address,
    "Google Maps": b.mapsUrl,
  };
}

export function exportToExcel(leads: Business[], filename = "leads.xlsx") {
  const ws = XLSX.utils.json_to_sheet(leads.map(toRow));
  ws["!cols"] = [
    { wch: 28 }, { wch: 18 }, { wch: 7 }, { wch: 8 }, { wch: 16 },
    { wch: 16 }, { wch: 28 }, { wch: 18 }, { wch: 30 }, { wch: 40 }, { wch: 40 },
  ];
  const wb = XLSX.utils.book_new();
  XLSX.utils.book_append_sheet(wb, ws, "Leads");
  XLSX.writeFile(wb, filename);
}

/** Best WhatsApp-capable number for a lead: explicit wa.me number first,
 * then any mobile-looking site phone, then the listed Maps phone. */
export function bestWhatsAppNumber(b: Business): string | null {
  const pick = b.whatsapp[0] || b.sitePhones[0] || b.phone || "";
  const digits = pick.replace(/[^\d]/g, "");
  return digits.length >= 7 ? digits : null;
}

export function whatsAppLink(number: string, message: string): string {
  const digits = number.replace(/[^\d]/g, "");
  return `https://wa.me/${digits}?text=${encodeURIComponent(message)}`;
}

/** Build a vCard (.vcf) file of all leads that have a usable number — import
 * straight into your phone contacts, then they show up in WhatsApp. */
export function exportToVcf(leads: Business[], filename = "leads.vcf") {
  const cards: string[] = [];
  for (const b of leads) {
    const num = bestWhatsAppNumber(b);
    if (!num) continue;
    const lines = [
      "BEGIN:VCARD",
      "VERSION:3.0",
      `FN:${b.name}`,
      `ORG:${b.name}`,
      `TEL;TYPE=CELL:+${num}`,
    ];
    if (b.emails[0]) lines.push(`EMAIL:${b.emails[0]}`);
    if (b.website) lines.push(`URL:${b.website}`);
    if (b.address) lines.push(`ADR:;;${b.address.replace(/\n/g, " ")};;;;`);
    lines.push("END:VCARD");
    cards.push(lines.join("\n"));
  }
  const blob = new Blob([cards.join("\n")], { type: "text/vcard;charset=utf-8" });
  triggerDownload(blob, filename);
  return cards.length;
}

function triggerDownload(blob: Blob, filename: string) {
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  a.remove();
  URL.revokeObjectURL(url);
}
