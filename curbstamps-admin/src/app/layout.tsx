import type { Metadata } from "next";
import Link from "next/link";
import "./globals.css";
import { currentAdmin } from "@/lib/auth";
import { logoutAction } from "./login/actions";

export const metadata: Metadata = {
  title: "Curb Stamps Admin",
  robots: { index: false, follow: false },
};

export default async function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  const admin = await currentAdmin();

  return (
    <html lang="en-AU">
      <body className="min-h-screen bg-paper text-ink">
        <div className="sm:flex">
          <aside className="shrink-0 border-b border-ink/10 px-4 py-4 sm:min-h-screen sm:w-56 sm:border-r sm:border-b-0 sm:py-8">
            <p className="text-[16px] font-extrabold">Curb Stamps</p>
            <nav className="mt-6 flex flex-col gap-1 text-[14px] font-semibold">
              <Link href="/orders" className="rounded-lg px-3 py-2 hover:bg-paper-2">
                Orders
              </Link>
            </nav>
            {admin && (
              <form action={logoutAction} className="mt-8">
                <p className="px-3 text-[12px] text-ink/50">{admin}</p>
                <button type="submit" className="mt-1 px-3 text-[12px] font-semibold underline">
                  Sign out
                </button>
              </form>
            )}
          </aside>
          <main className="min-w-0 flex-1 px-4 py-8 sm:px-6">
            <div className="mx-auto max-w-4xl">{children}</div>
          </main>
        </div>
      </body>
    </html>
  );
}
