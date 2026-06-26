import type { NextRequest } from "next/server";
import Anthropic from "@anthropic-ai/sdk";
import type { DraftRequest, DraftResponse } from "@/lib/types";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";
export const maxDuration = 60;

const MODEL = process.env.ANTHROPIC_MODEL || "claude-opus-4-8";

const SYSTEM = `You are an expert B2B sales copywriter helping a freelancer / agency reach out to potential clients found on Google Maps and social media.

Write outreach that is:
- Short, warm, and human — never spammy or templated-sounding.
- Specific to the prospect: reference their business name and the concrete observation given (e.g. "no website", low rating, the exact thing they asked for).
- Value-first: lead with how you can help them, not with how great you are.
- Honest and compliant: no false claims, no pressure tactics.

Always reply with ONLY a JSON object, no prose or markdown, in exactly this shape:
{
  "emailSubject": "string (<= 60 chars)",
  "emailBody": "string (3-5 short sentences, with a clear soft call-to-action)",
  "whatsapp": "string (1-2 sentences, casual, <= 320 chars)",
  "dm": "string (1-2 sentences, suited to a LinkedIn/Instagram DM)"
}`;

function extractJson(text: string): DraftResponse | null {
  const start = text.indexOf("{");
  const end = text.lastIndexOf("}");
  if (start < 0 || end <= start) return null;
  try {
    const obj = JSON.parse(text.slice(start, end + 1));
    return {
      emailSubject: String(obj.emailSubject || ""),
      emailBody: String(obj.emailBody || ""),
      whatsapp: String(obj.whatsapp || ""),
      dm: String(obj.dm || ""),
    };
  } catch {
    return null;
  }
}

export async function POST(req: NextRequest) {
  if (!process.env.ANTHROPIC_API_KEY) {
    return Response.json(
      {
        error:
          "AI drafting needs an Anthropic API key. Add ANTHROPIC_API_KEY to .env.local (see .env.example) and restart.",
      },
      { status: 400 },
    );
  }

  let body: DraftRequest;
  try {
    body = (await req.json()) as DraftRequest;
  } catch {
    return Response.json({ error: "Invalid JSON" }, { status: 400 });
  }

  const service = String(body?.service || "").trim();
  const targetName = String(body?.targetName || "there").trim();
  const context = String(body?.context || "").trim();
  const bookingLink = String(body?.bookingLink || "").trim();
  const kind = body?.kind === "intent" ? "intent" : "lead";

  if (!service) {
    return Response.json({ error: "Tell the app what service you offer first." }, { status: 400 });
  }

  const userPrompt = [
    `I offer: ${service}.`,
    kind === "intent"
      ? `I found this person publicly asking for help online. Their post / details:`
      : `I found this business on Google Maps. Details:`,
    `--- ${targetName} ---`,
    context || "(no extra detail)",
    bookingLink
      ? `Weave in this booking link naturally so they can grab a time: ${bookingLink}`
      : `I don't have a booking link — end with a simple question that invites a reply.`,
    `Write the outreach now.`,
  ].join("\n");

  try {
    const client = new Anthropic();
    const msg = await client.messages.create({
      model: MODEL,
      max_tokens: 1200,
      system: SYSTEM,
      messages: [{ role: "user", content: userPrompt }],
    });

    const text = msg.content
      .filter((b): b is Anthropic.TextBlock => b.type === "text")
      .map((b) => b.text)
      .join("");

    const draft = extractJson(text);
    if (!draft) {
      return Response.json({ error: "Could not parse the AI response. Try again." }, { status: 502 });
    }
    return Response.json(draft);
  } catch (err: any) {
    const status = err?.status === 401 ? 401 : 502;
    return Response.json(
      { error: err?.message || "AI request failed", model: MODEL },
      { status },
    );
  }
}
