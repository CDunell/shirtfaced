import { PageShell, Prose, Section } from "@/components/PageShell";
import { FREE_SHIPPING_THRESHOLD } from "@/lib/products";
import { money } from "@/lib/money";
import { shipping } from "@/lib/content-data.generated";

export const metadata = {
  title: "Shipping — Shirtfaced",
  description: "Where we ship, what it costs, and how long it takes.",
};

export default function ShippingPage() {
  const RATES = [
    { name: shipping.standardName, time: shipping.standardTime, price: shipping.standardPrice },
    { name: shipping.expressName, time: shipping.expressTime, price: shipping.expressPrice },
    {
      name: "Free standard",
      time: "5–7 business days",
      price: `Orders over ${money(FREE_SHIPPING_THRESHOLD)}`,
    },
  ];

  return (
    <PageShell title="shipping" intro={shipping.intro}>
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
            <p>{shipping.whereP1}</p>
            <p>{shipping.whereP2}</p>
          </Prose>
        </Section>

        <Section heading="Tracking">
          <Prose>
            <p>{shipping.trackingP1}</p>
          </Prose>
        </Section>

        <Section heading="Packaging">
          <Prose>
            <p>{shipping.packagingP1}</p>
          </Prose>
        </Section>
      </div>
    </PageShell>
  );
}
