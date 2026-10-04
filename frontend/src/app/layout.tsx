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
    <html lang="en" className="dark h-full" style={{ colorScheme: "dark" }} suppressHydrationWarning>
      <head>
        <script
          dangerouslySetInnerHTML={{
            __html: `
              (function() {
                document.documentElement.classList.add('dark');
              })();
            `,
          }}
        />
      </head>
      <body className="min-h-screen bg-slate-950 text-slate-100 antialiased font-sans flex flex-col">
        {children}
      </body>
    </html>
  );
}
