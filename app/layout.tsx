import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "LMS | Varun",
  description: "Leave management system for Dreambus.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className="">{children}</body>
    </html>
  );
}
