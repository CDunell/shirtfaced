import type { Metadata, Viewport } from "next";
import { Anton, Space_Grotesk } from "next/font/google";
import "./globals.css";
import { CartProvider } from "@/lib/cart-context";
import { Header } from "@/components/Header";
import { PaperGrain } from "@/components/Texture";
import { LINE_THREE, TAGLINES } from "@/lib/taglines";

/* Reference form from docs/foundations/BRAND_VOICE.md §3 — the first pair in
   the rotation, not a hand-typed line. Pulling it from the same source the
   hero reads from is the fix for the two disagreeing with each other. */
const REFERENCE_LINE = `${TAGLINES[0].beatOne} ${TAGLINES[0].beatTwo} ${LINE_THREE}`;

const anton = Anton({
  variable: "--font-anton",
  subsets: ["latin"],
  weight: "400",
  display: "swap",
});

const spaceGrotesk = Space_Grotesk({
  variable: "--font-space-grotesk",
  subsets: ["latin"],
  display: "swap",
});

export const metadata: Metadata = {
  title: `shirtfaced — ${REFERENCE_LINE}`,
  description:
    "Graphic tees for people with questionable judgement and excellent taste. Designed in Australia. Printed properly.",
  manifest: "/site.webmanifest",
  openGraph: {
    title: "shirtfaced",
    description: REFERENCE_LINE,
    type: "website",
  },
};

export const viewport: Viewport = {
  themeColor: "#0d0d0d",
  width: "device-width",
  initialScale: 1,
  viewportFit: "cover",
};

export default function RootLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  return (
    <html
      lang="en-AU"
      className={`${anton.variable} ${spaceGrotesk.variable} h-full`}
    >
      <head>
        {/*
          Picks the tagline BEFORE first paint, so there's no flash of the
          wrong line and no hydration mismatch — React renders all six and CSS
          decides. Per session: consistent while browsing and on
          back-navigation, but a new line on the next visit. Change
          sessionStorage to localStorage for per-device, or key it on the date
          for per-day.
        */}
        <script
          dangerouslySetInnerHTML={{
            __html: `(function(){try{var n=6,k="sf-tag",v=sessionStorage.getItem(k);if(v===null){v=String(Math.floor(Math.random()*n));sessionStorage.setItem(k,v)}document.documentElement.setAttribute("data-tag",v)}catch(e){document.documentElement.setAttribute("data-tag","0")}})()`,
          }}
        />
      </head>
      <body className="min-h-full bg-paper text-ink">
        <PaperGrain />
        <CartProvider>
          <a
            href="#main"
            className="sr-only focus:not-sr-only focus:fixed focus:top-3 focus:left-3 focus:z-50 focus:rounded-[14px] focus:bg-ink focus:px-4 focus:py-2 focus:text-sm focus:text-paper"
          >
            Skip to content
          </a>
          <Header />
          <main id="main">{children}</main>
        </CartProvider>
      </body>
    </html>
  );
}
