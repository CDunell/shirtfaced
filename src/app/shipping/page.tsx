import { PageShell, Prose, Section } from "@/components/PageShell";
import { FREE_SHIPPING_THRESHOLD } from "@/lib/products";
import { money } from "@/lib/money";

export const metadata = {
  title: "Shipping — Shirtfaced",
  description: "Where we ship, what it costs, and how long it takes.",
};

const RATES = [
  { name: "Standard", time: "3–5 business days", price: "$10.00" },
  { name: "Express", time: "1–2 business days", price: "$15.00" },
  {
    name: "Free standard",
    time: "5–7 business days",
    price: `Orders over ${money(FREE_SHIPPING_THRESHOLD)}`,
  },
];

export default function ShippingPage() {
  return (
    <PageShell
      title="shipping"
      intro="Designed in Australia, printed and shipped from wherever gets it to you fastest."
    >
      <ul className="flex flex-col gap-3">
        {RATES.map((r) => (
          <li
            key={r.name}
            className="flex items-baseline justify-between gap-4 rounded-[20px] border border-ink/12 px-5 py-4"
          >
            <span>
              <span className="display block text-[20px]">{r.name}</span>
              <span className="text-[14px] text-grey-dark">{r.time}</span>
            </span>
            <span className="shrink-0 text-[15px] font-semibold tabular-nums">
              {r.price}
            </span>
          </li>
        ))}
      </ul>

      <div className="mt-8 flex flex-col gap-8">
        <Section heading="Where we ship">
          <Prose>
            <p>
              Australia-wide, including WA and the Territories. New Zealand ships
              at a flat $18 and takes 5–10 business days.
            </p>
            <p>
              Everywhere else — we&apos;re working on it. If you&apos;re
              overseas and desperate, get in touch and we&apos;ll quote you
              properly rather than guess.
            </p>
          </Prose>
        </Section>

        <Section heading="Tracking">
          <Prose>
            <p>
              Every order gets a tracking number by email the moment it leaves.
              If it hasn&apos;t arrived within the window above, tell us and
              we&apos;ll chase it — you shouldn&apos;t have to argue with a
              courier on our behalf.
            </p>
          </Prose>
        </Section>

        <Section heading="Packaging">
          <Prose>
            <p>
              Recycled mailers, no plastic filler, no branded tissue paper that
              goes straight in the bin. The mailer is the packaging.
            </p>
          </Prose>
        </Section>
      </div>
    </PageShell>
  );
}
