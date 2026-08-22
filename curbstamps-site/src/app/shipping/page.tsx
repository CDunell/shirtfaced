import { PageShell, Section, Prose } from "@/components/PageShell";
import { FREE_SHIPPING_THRESHOLD } from "@/lib/products";
import { SHIPPING_METHODS } from "@/lib/checkout-pricing";
import { money } from "@/lib/money";

export const metadata = { title: "Shipping — Curb Stamps" };

export default function ShippingPage() {
  return (
    <PageShell title="shipping" intro="Printed to order, then posted — here's what that means for timing.">
      <Section heading="Methods">
        <ul className="mt-1 flex flex-col gap-3">
          {SHIPPING_METHODS.map((m) => (
            <li key={m.key} className="flex items-baseline justify-between">
              <span>
                <span className="block text-[15px] font-bold">{m.name}</span>
                <span className="text-[13px] text-grey-dark">{m.time}</span>
              </span>
              <span className="text-[15px] font-bold">{money(m.price)}</span>
            </li>
          ))}
        </ul>
        <p className="mt-4 text-[13px] text-grey-dark">
          Free standard shipping on orders over {money(FREE_SHIPPING_THRESHOLD)}.
        </p>
      </Section>
      <Section heading="Where we ship">
        <Prose>
          <p>Australia-wide. International shipping isn&apos;t open yet — it&apos;s on the list.</p>
        </Prose>
      </Section>
      <Section heading="Tracking">
        <Prose>
          <p>A tracking link goes out by email the moment your order ships.</p>
        </Prose>
      </Section>
      <Section heading="Why the wait?">
        <Prose>
          <p>
            Nothing sits pre-printed in a warehouse — each order is produced once it comes
            in, which is what makes 60 creatures possible without guessing which twelve
            will sell.
          </p>
        </Prose>
      </Section>
    </PageShell>
  );
}
