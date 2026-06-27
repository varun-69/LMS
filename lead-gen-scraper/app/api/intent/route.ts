import type { NextRequest } from "next/server";
import { gatherIntent } from "@/lib/intentSources";
import { buildIntentLinks } from "@/lib/intentLinks";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";

export async function POST(req: NextRequest) {
  let body: any;
  try {
    body = await req.json();
  } catch {
    return Response.json({ error: "Invalid JSON" }, { status: 400 });
  }

  const service = String(body?.service || "").trim();
  const location = String(body?.location || "").trim();
  const timeframe = ["day", "week", "month"].includes(body?.timeframe)
    ? body.timeframe
    : "day";

  if (!service) {
    return Response.json({ error: "A service / niche is required" }, { status: 400 });
  }

  const links = buildIntentLinks(service, location);

  try {
    const { posts, warnings, counts } = await gatherIntent(service, location, timeframe);
    return Response.json({ posts, links, counts, warning: warnings.join(" · ") });
  } catch (err: any) {
    // A source failing shouldn't break the search-link feature.
    return Response.json({ posts: [], links, warning: err?.message || "Intent search failed" });
  }
}
