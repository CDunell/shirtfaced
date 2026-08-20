import Link from "next/link";
import { Card } from "@/components/ui";

const PAGES = [
  { href: "/content/home", label: "Home", note: "Trust bar, promo banner, newsletter heading" },
  { href: "/content/about", label: "About", note: "The idea, how they're made, what we won't do, who's behind it" },
  { href: "/content/shipping", label: "Shipping", note: "Rates, where we ship, tracking, packaging" },
  { href: "/content/returns", label: "Returns", note: "How it works, exchanges, faults, exclusions" },
  { href: "/content/contact", label: "Contact", note: "Intro, email address, wholesale, press, bottom line" },
  { href: "/content/size-guide", label: "Size guide", note: "Measurements table, how to measure, between sizes, care" },
  { href: "/content/product", label: "Product page", note: "The four-item feature list shown on every product" },
  { href: "/content/account", label: "Account", note: "Intro and the three account benefits" },
  { href: "/content/more", label: "More", note: "Footer callout heading and subline" },
  { href: "/content/garment-care", label: "Garment care", note: "Washing, drying, print care, storage" },
  { href: "/content/faq", label: "FAQ", note: "Intro plus the question list" },
];

export default function ContentIndexPage() {
  return (
    <div className="flex flex-col gap-6">
      <h1 className="display text-[40px]">Site content</h1>
      <div className="flex flex-col gap-3">
        {PAGES.map((p) => (
          <Link key={p.href} href={p.href}>
            <Card className="press hover:bg-paper-2">
              <p className="font-semibold">{p.label}</p>
              <p className="mt-1 text-[13px] text-ink/50">{p.note}</p>
            </Card>
          </Link>
        ))}
      </div>
    </div>
  );
}
