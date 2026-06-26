import type { NextRequest } from "next/server";
import { scrapeGoogleMaps } from "@/lib/scraper";
import type { StreamEvent } from "@/lib/types";

// Playwright needs the Node.js runtime and plenty of time.
export const runtime = "nodejs";
export const dynamic = "force-dynamic";
export const maxDuration = 300;

export async function POST(req: NextRequest) {
  let body: any;
  try {
    body = await req.json();
  } catch {
    return new Response("Invalid JSON body", { status: 400 });
  }

  const niche = String(body?.niche || "").trim();
  const location = String(body?.location || "").trim();
  const limit = Math.min(Math.max(parseInt(body?.limit, 10) || 30, 1), 200);
  const enrich = body?.enrich !== false;

  if (!niche || !location) {
    return new Response("Both 'niche' and 'location' are required", { status: 400 });
  }

  const encoder = new TextEncoder();
  const stream = new ReadableStream<Uint8Array>({
    async start(controller) {
      const send = (event: StreamEvent) => {
        try {
          controller.enqueue(encoder.encode(JSON.stringify(event) + "\n"));
        } catch {
          /* stream already closed */
        }
      };

      try {
        const count = await scrapeGoogleMaps(
          { niche, location, limit, enrich },
          (b) => send({ type: "lead", data: b }),
          (message) => send({ type: "status", message }),
          req.signal,
        );
        send({ type: "done", count });
      } catch (err: any) {
        send({ type: "error", message: err?.message || "Scrape failed" });
      } finally {
        controller.close();
      }
    },
  });

  return new Response(stream, {
    headers: {
      "Content-Type": "application/x-ndjson; charset=utf-8",
      "Cache-Control": "no-cache, no-transform",
      Connection: "keep-alive",
    },
  });
}
