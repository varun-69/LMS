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
  /** Emails discovered on the business website (may be empty). */
  emails: string[];
  /** WhatsApp numbers found via wa.me / api.whatsapp.com links on the site. */
  whatsapp: string[];
  /** Extra phone numbers (often mobiles) scraped from the website. */
  sitePhones: string[];
}

export interface ScrapeParams {
  niche: string;
  location: string;
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
