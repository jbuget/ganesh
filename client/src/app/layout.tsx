import type { Metadata } from "next";

import { AppSidebar } from "@/components/organisms/AppSidebar";
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
        <QueryProvider>
          <div className="flex min-h-screen">
            <AppSidebar />
            <div className="min-w-0 flex-1">{children}</div>
          </div>
        </QueryProvider>
      </body>
    </html>
  );
}
