import type { Metadata } from "next";
import { GeistSans } from "geist/font/sans";
import "./globals.css";
import { Providers } from "@/lib/providers";
import { CompanyProvider } from "@/lib/company-context";
import { AppNav } from "@/components/staggered-menu/AppNav";

export const metadata: Metadata = {
  title: "MicroPayroll",
  description: "Open-source payroll for micro-businesses",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body className={`${GeistSans.className} bg-[#120F17] text-slate-100 antialiased`}>
        <Providers>
          <CompanyProvider>
            <div className="relative min-h-screen">
              <AppNav />
              <main className="min-h-screen pt-20">{children}</main>
            </div>
          </CompanyProvider>
        </Providers>
      </body>
    </html>
  );
}
