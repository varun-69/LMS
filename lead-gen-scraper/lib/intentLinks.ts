import type { IntentLink } from "./types";

/**
 * Build one-click search links that open each platform's OWN search,
 * pre-filtered to the service + buying-intent keywords (+ location).
 *
 * This is the free, ToS-safe alternative to scraping logged-in platforms:
 * you're already signed in, so clicking the link shows you the real intent
 * posts directly on LinkedIn / Instagram / Threads / Naukri / X / Google.
 */
export function buildIntentLinks(service: string, location: string): IntentLink[] {
  const svc = service.trim();
  const loc = location.trim();
  const intent = `("looking for" OR "need a" OR "recommend" OR "anyone know")`;
  const enc = (s: string) => encodeURIComponent(s);

  const links: IntentLink[] = [
    {
      platform: "LinkedIn",
      label: "Recent posts",
      url: `https://www.linkedin.com/search/results/content/?keywords=${enc(
        `${intent} ${svc} ${loc}`,
      )}&sortBy=%22date_posted%22`,
    },
    {
      platform: "X / Twitter",
      label: "Latest tweets",
      url: `https://x.com/search?q=${enc(`${intent} ${svc} ${loc}`)}&f=live`,
    },
    {
      platform: "Google",
      label: "Forums & posts (past 24h)",
      url: `https://www.google.com/search?q=${enc(
        `${intent} ${svc} ${loc} (site:reddit.com OR site:quora.com OR site:linkedin.com)`,
      )}&tbs=qdr:d`,
    },
    {
      platform: "Instagram",
      label: "Hashtag search",
      url: `https://www.instagram.com/explore/tags/${enc(
        svc.replace(/[^a-z0-9]/gi, "").toLowerCase() || "smallbusiness",
      )}/`,
    },
    {
      platform: "Threads",
      label: "Search",
      url: `https://www.threads.net/search?q=${enc(`${svc} ${loc}`)}&serp_type=default`,
    },
    {
      platform: "Naukri",
      label: "Companies hiring (proxy for need)",
      url: `https://www.naukri.com/${enc(svc.replace(/\s+/g, "-").toLowerCase())}-jobs${
        loc ? `-in-${enc(loc.replace(/\s+/g, "-").toLowerCase())}` : ""
      }`,
    },
    {
      platform: "Facebook",
      label: "Recent posts",
      url: `https://www.facebook.com/search/posts/?q=${enc(`${intent} ${svc} ${loc}`)}`,
    },
  ];

  return links;
}
