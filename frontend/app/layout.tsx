import type { Metadata } from "next";
import "./globals.css";
import Sidebar from "@/components/Sidebar";
import Header from "@/components/Header";

export const metadata: Metadata = {
  title: "SIH26147 — Automated RF Signal Analyzer",
  description: "Turn raw IQ and WAV recordings into actionable signal intelligence. Automated modulation classification, parameter extraction, demodulation, and report generation.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="dark">
      <body>
        <Sidebar />
        <Header />
        <main style={{
          marginLeft: 'var(--sidebar-width)',
          marginTop: 'var(--header-height)',
          minHeight: 'calc(100vh - var(--header-height))',
          padding: '24px',
        }}>
          {children}
        </main>
      </body>
    </html>
  );
}
