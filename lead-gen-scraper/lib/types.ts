export interface Business {
  /** Stable-ish id derived from the Google Maps place URL. */
  id: string;
  name: string;
  category: string;
  address: string;
  /** Phone number exactly as listed on Google Maps. */
  phone: string;
  website: string;
  rating: string;
  reviews: string;
  mapsUrl: string;
  /** Which of the searched niches this listing matched. */
  niche: string;
  /** Emails discovered on the business website (may be empty). */
  emails: string[];
  /** WhatsApp numbers found via wa.me / api.whatsapp.com links on the site. */
  whatsapp: string[];
  /** Extra phone numbers (often mobiles) scraped from the website. */
  sitePhones: string[];
}

export interface ScrapeParams {
  /** One or more niches to search (comma-separated input is split upstream). */
  niches: string[];
  location: string;
  /** Max results per niche. */
  limit: number;
  /** Whether to visit each business website to find email / WhatsApp. */
  enrich: boolean;
}

/** A line of the NDJSON stream returned by /api/scrape. */
export type StreamEvent =
  | { type: "status"; message: string }
  | { type: "lead"; data: Business }
  | { type: "done"; count: number }
  | { type: "error"; message: string };

/** A buying-intent post found on Reddit (the only free, no-login source). */
export interface IntentPost {
  id: string;
  source: "reddit";
  title: string;
  snippet: string;
  author: string;
  channel: string; // subreddit, e.g. r/smallbusiness
  url: string;
  createdUtc: number; // epoch seconds
}

/** A one-click search link that opens a platform's own search, pre-filtered. */
export interface IntentLink {
  platform: string;
  label: string;
  url: string;
}

export interface DraftRequest {
  /** What you sell, e.g. "web development & digital marketing". */
  service: string;
  /** Target name (business or person). */
  targetName: string;
  /** Free-form context: category, rating, "no website", the intent post text… */
  context: string;
  /** Optional booking link to weave into the message. */
  bookingLink?: string;
  /** "lead" (Google Maps business) or "intent" (someone asking for help). */
  kind: "lead" | "intent";
}

export interface DraftResponse {
  emailSubject: string;
  emailBody: string;
  whatsapp: string;
  dm: string;
}
