import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Investment Reviewer",
  description: "Monthly financial statement analysis powered by RAG + LLM",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className="min-h-screen bg-gray-950 text-gray-100">
        <nav className="border-b border-gray-800 bg-gray-900 px-6 py-4">
          <div className="mx-auto flex max-w-6xl items-center justify-between">
            <span className="text-lg font-semibold tracking-tight text-white">
              Investment Reviewer
            </span>
            <div className="flex gap-6 text-sm text-gray-400">
              <a href="/" className="hover:text-white transition-colors">
                Dashboard
              </a>
              <a href="/upload" className="hover:text-white transition-colors">
                Upload
              </a>
              <a href="/compare" className="hover:text-white transition-colors">
                Compare
              </a>
              <a href="/ask" className="hover:text-white transition-colors">
                Ask
              </a>
            </div>
          </div>
        </nav>
        <main className="mx-auto max-w-6xl px-6 py-8">{children}</main>
      </body>
    </html>
  );
}
