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
    <html lang="en" className="h-full dark" suppressHydrationWarning>
      <head>
        <script
          dangerouslySetInnerHTML={{
            __html: `
              (function() {
                try {
                  const saved = localStorage.getItem('ethioformat-theme');
                  if (saved === 'light') {
                    document.documentElement.classList.remove('dark');
                  } else {
                    document.documentElement.classList.add('dark');
                  }
                } catch (e) {
                  document.documentElement.classList.add('dark');
                }
              })();
            `,
          }}
        />
      </head>
      <body className="min-h-screen bg-slate-50 dark:bg-slate-950 text-slate-900 dark:text-slate-100 antialiased font-sans flex flex-col transition-colors duration-200">
        {children}
      </body>
    </html>
  );
}
