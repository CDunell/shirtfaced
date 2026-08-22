import Link from "next/link";
import { IconArrowLeft } from "./Icons";

/** Consistent frame for content pages — About, FAQ, Terms, etc. */
export function PageShell({
  title,
  intro,
  back = { href: "/", label: "Home" },
  children,
}: {
  title: string;
  intro?: string;
  back?: { href: string; label: string } | null;
  children: React.ReactNode;
}) {
  return (
    <div className="mx-auto max-w-2xl px-4 pt-4 pb-16 sm:px-6">
      {back && (
        <Link
          href={back.href}
          className="press -ml-2 inline-flex h-11 items-center gap-2 rounded-full px-3 text-[13px] font-bold text-grey-dark"
        >
          <IconArrowLeft className="h-4 w-4" />
          {back.label}
        </Link>
      )}

      <h1 className="display mt-3 text-[13vw] leading-[0.9] sm:text-[54px]">{title}</h1>

      {intro && <p className="mt-4 max-w-[46ch] text-[16px] leading-relaxed text-ink/70">{intro}</p>}

      <div className="mt-8">{children}</div>
    </div>
  );
}

export function Prose({ children }: { children: React.ReactNode }) {
  return <div className="flex max-w-[54ch] flex-col gap-5 text-[16px] leading-relaxed text-ink/80">{children}</div>;
}

export function Section({ heading, children }: { heading: string; children: React.ReactNode }) {
  return (
    <section className="border-t-2 border-ink/10 pt-6">
      <h2 className="display text-[22px]">{heading}</h2>
      <div className="mt-3">{children}</div>
    </section>
  );
}
