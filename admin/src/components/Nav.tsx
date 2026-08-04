import Link from "next/link";
import { logoutAction } from "@/app/actions";

export function Nav({
  adminEmail,
  studioUrl,
}: {
  adminEmail: string | null;
  studioUrl: string;
}) {
  return (
    <header className="border-b border-ink/10 bg-paper/95 backdrop-blur">
      <div className="mx-auto flex h-16 max-w-5xl items-center justify-between px-4 sm:px-6">
        <Link href="/products" className="wordmark text-[22px] font-display">
          shirtfaced <span className="text-ink/40">/ admin</span>
        </Link>

        <nav className="flex items-center gap-1 text-[13px] font-semibold tracking-wide uppercase">
          <Link
            href="/products"
            className="press rounded-[14px] px-3 py-2 hover:bg-paper-2"
          >
            Products
          </Link>
          <Link
            href="/content"
            className="press rounded-[14px] px-3 py-2 hover:bg-paper-2"
          >
            Content
          </Link>
          <a
            href={studioUrl}
            target="_blank"
            rel="noopener noreferrer"
            className="press rounded-[14px] px-3 py-2 hover:bg-paper-2"
          >
            Studio ↗
          </a>

          {adminEmail && (
            <form action={logoutAction} className="ml-2">
              <button
                type="submit"
                className="press rounded-[14px] border border-ink/15 px-3 py-2 text-ink/70 hover:bg-paper-2"
              >
                Log out
              </button>
            </form>
          )}
        </nav>
      </div>
    </header>
  );
}
