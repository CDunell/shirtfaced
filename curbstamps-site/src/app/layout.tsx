import type { Metadata, Viewport } from "next";
import { Baloo_2, Nunito } from "next/font/google";
import "./globals.css";
import { CartProvider } from "@/lib/cart-context";
import { Header } from "@/components/Header";
import { Footer } from "@/components/Footer";

const baloo = Baloo_2({
  variable: "--font-baloo",
  subsets: ["latin"],
  weight: ["600", "700", "800"],
  display: "swap",
});

const nunito = Nunito({
  variable: "--font-nunito",
  subsets: ["latin"],
  display: "swap",
});

export const metadata: Metadata = {
  title: "Curb Stamps — little creatures on little clothes",
  description:
    "Kids tees, hoodies and caps stamped with 60 (and counting) little creatures. Toddler to teen. Screen-printed properly.",
  manifest: "/site.webmanifest",
  icons: {
    icon: [
      { url: "/brand-icon/16", sizes: "16x16", type: "image/png" },
      { url: "/brand-icon/32", sizes: "32x32", type: "image/png" },
      { url: "/brand-icon/48", sizes: "48x48", type: "image/png" },
      { url: "/brand-icon/192", sizes: "192x192", type: "image/png" },
      { url: "/brand-icon/512", sizes: "512x512", type: "image/png" },
    ],
    apple: [{ url: "/brand-icon/180", sizes: "180x180", type: "image/png" }],
  },
  openGraph: {
    title: "Curb Stamps",
    description: "Little creatures on little clothes.",
    type: "website",
  },
};

export const viewport: Viewport = {
  themeColor: "#000000",
  width: "device-width",
  initialScale: 1,
  viewportFit: "cover",
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en-AU" className={`${baloo.variable} ${nunito.variable} h-full`}>
      <body className="min-h-full bg-paper text-ink">
        <CartProvider>
          <a
            href="#main"
            className="sr-only focus:not-sr-only focus:fixed focus:top-3 focus:left-3 focus:z-50 focus:rounded-full focus:bg-ink focus:px-4 focus:py-2 focus:text-sm focus:text-paper"
          >
            Skip to content
          </a>
          <Header />
          <main id="main">{children}</main>
          <Footer />
        </CartProvider>
      </body>
    </html>
  );
}
