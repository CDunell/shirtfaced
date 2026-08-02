import type { Metadata, Viewport } from "next";
import { Anton, Space_Grotesk } from "next/font/google";
import "./globals.css";
import { CartProvider } from "@/lib/cart-context";
import { Header } from "@/components/Header";
import { BottomNav } from "@/components/BottomNav";
import { PaperGrain } from "@/components/Texture";

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
  title: "Shirtfaced — Good times. Bad decisions. Zero regrets.",
  description:
    "Graphic tees for people with questionable judgement and excellent taste. Designed in Australia. Printed properly.",
  openGraph: {
    title: "Shirtfaced",
    description: "Good times. Bad decisions. Zero regrets.",
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
          {/* pb clears the fixed bottom nav + iOS home indicator */}
          <main
            id="main"
            className="pb-[calc(84px+env(safe-area-inset-bottom))]"
          >
            {children}
          </main>
          <BottomNav />
        </CartProvider>
      </body>
    </html>
  );
}
