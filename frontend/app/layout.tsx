import type { Metadata } from "next";
import { Inter, Space_Grotesk } from "next/font/google";
import Script from "next/script";
import "./globals.css";
import { Providers } from "@/app/providers";

const inter = Inter({
  subsets: ["latin"],
  variable: "--font-inter",
  weight: ["400", "500"],
  display: "swap",
});

const spaceGrotesk = Space_Grotesk({
  subsets: ["latin"],
  variable: "--font-space-grotesk",
  weight: ["500", "600"],
  display: "swap",
});

export const metadata: Metadata = {
  title: "Metrika — Analytics Simplified",
  description: "Cloud-hosted, web analytics you control.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className={`${inter.variable} ${spaceGrotesk.variable}`}>
      <body>
        <Providers>{children}</Providers>
        <Script
          strategy="beforeInteractive"
          data-domain="metrika-five.vercel.app"
          data-token="00ad7e68c12c4d1196183a034d03c6cf"
          src="https://metrika-five.vercel.app/js/tracker.js"
        />
      </body>
    </html>
  );
}
