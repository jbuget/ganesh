import type { Metadata } from "next";

import { QueryProvider } from "@/lib/query-provider";

import "./globals.css";
import { Geist } from "next/font/google";
import { cn } from "@/lib/utils";

const geist = Geist({ subsets: ["latin"], variable: "--font-sans" });

export const metadata: Metadata = {
  title: "Ganesh — WAAT",
  description: "Suivi du temps passé par projet",
};

export default function RootLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="fr" className={cn("font-sans", geist.variable)}>
      <body className="bg-slate-50 text-slate-900 antialiased">
        {/* The sidebar is not here but in the (app) group: it belongs to the
            screens one reaches signed in, not to the page that asks. */}
        <QueryProvider>{children}</QueryProvider>
      </body>
    </html>
  );
}
