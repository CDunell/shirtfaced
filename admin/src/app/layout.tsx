import type { Metadata } from "next";
import { Anton, Space_Grotesk } from "next/font/google";
import "./globals.css";
import { Sidebar } from "@/components/Sidebar";
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
        <div className="sm:flex">
          <Sidebar adminEmail={admin} studioUrl={process.env.STUDIO_URL ?? "#"} />
          <main className="min-w-0 flex-1 px-4 py-8 sm:px-6">
            <div className="mx-auto max-w-5xl">{children}</div>
          </main>
        </div>
      </body>
    </html>
  );
}
