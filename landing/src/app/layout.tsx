import type { Metadata } from "next";
import { Source_Serif_4, IBM_Plex_Sans, IBM_Plex_Mono } from "next/font/google";
import "./globals.css";

const serif = Source_Serif_4({
  subsets: ["latin"],
  variable: "--font-source-serif",
  weight: ["400", "600", "700"],
  style: ["normal", "italic"],
  display: "swap",
});

const sans = IBM_Plex_Sans({
  subsets: ["latin"],
  variable: "--font-plex-sans",
  weight: ["300", "400", "500", "600"],
  display: "swap",
});

const mono = IBM_Plex_Mono({
  subsets: ["latin"],
  variable: "--font-plex-mono",
  weight: ["400", "500"],
  display: "swap",
});

export const metadata: Metadata = {
  title: "ATLS — Agentic Trauma Life Support",
  description:
    "Qwen2.5-VL-72B in full BF16 on a single AMD MI300X. Multilingual agentic trauma-triage decision-support. Built for the AMD Developer Hackathon, May 2026, by an emergency physician.",
  authors: [{ name: "0xNoramiya" }],
  openGraph: {
    title: "ATLS — Agentic Trauma Life Support",
    description:
      "Qwen2.5-VL-72B in full BF16 on a single AMD MI300X. Multilingual agentic trauma-triage decision-support.",
    type: "website",
  },
  twitter: {
    card: "summary_large_image",
    title: "ATLS — Agentic Trauma Life Support",
    description:
      "Qwen2.5-VL-72B in full BF16 on a single AMD MI300X. Multilingual agentic trauma-triage decision-support.",
  },
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html
      lang="en"
      className={`${serif.variable} ${sans.variable} ${mono.variable}`}
    >
      <body className="bg-paper text-ink font-body antialiased">
        <div className="relative z-[2]">{children}</div>
      </body>
    </html>
  );
}
