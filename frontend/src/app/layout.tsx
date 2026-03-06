import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "GrowthOS — AI-Powered Twitter Growth Platform",
  description: "Real-time virality modeling, AI content generation, smart scheduling, and closed-loop growth analytics.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
