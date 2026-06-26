import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Lead Gen Scraper — Google Maps leads, free",
  description:
    "Search a niche + location, scrape business contacts from Google Maps, export to Excel or WhatsApp.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
