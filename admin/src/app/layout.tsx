import type { Metadata } from "next";
import { Anton, Space_Grotesk } from "next/font/google";
import "./globals.css";
import { Nav } from "@/components/Nav";
import { currentAdmin } from "@/lib/auth";

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
  title: "Shirtfaced Admin",
  robots: { index: false, follow: false },
};

export default async function RootLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  const admin = await currentAdmin();

  return (
    <html lang="en-AU" className={`${anton.variable} ${spaceGrotesk.variable}`}>
      <body className="min-h-screen bg-paper text-ink">
        <Nav adminEmail={admin} studioUrl={process.env.STUDIO_URL ?? "#"} />
        <main className="mx-auto max-w-5xl px-4 py-8 sm:px-6">{children}</main>
      </body>
    </html>
  );
}
