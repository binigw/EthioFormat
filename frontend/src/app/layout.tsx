import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "EthioFormat — Automated Ethiopian Thesis Formatting SaaS",
  description: "Automated, standard thesis formatting for Ethiopian universities with instant 3-page preview and secure payment release.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="h-full">
      <body className="min-h-screen bg-slate-50 antialiased font-sans flex flex-col">
        {children}
      </body>
    </html>
  );
}
