import { PageShell, Prose, Section } from "@/components/PageShell";

export const metadata = {
  title: "Returns — Shirtfaced",
  description: "30 days, unworn, no interrogation.",
};

export default function ReturnsPage() {
  return (
    <PageShell
      title="returns"
      intro="Thirty days. Unworn, unwashed, tags on. We won't ask why."
    >
      <div className="flex flex-col gap-8">
        <Section heading="How it works">
          <ol className="flex flex-col gap-4">
            {[
              ["Email us", "Order number and which items are coming back. That's the whole form."],
              ["We send a label", "Prepaid, within one business day."],
              ["Post it", "Any Australia Post box. Keep the receipt until it's refunded."],
              ["Refunded", "Back to your original payment method within 5 business days of arrival."],
            ].map(([a, b], i) => (
              <li key={a} className="flex gap-4">
                <span className="display grid h-9 w-9 shrink-0 place-items-center rounded-full bg-ink text-[16px] text-paper">
                  {i + 1}
                </span>
                <span className="pt-1 text-[16px] leading-relaxed">
                  <strong>{a}</strong>
                  <br />
                  <span className="text-ink/70">{b}</span>
                </span>
              </li>
            ))}
          </ol>
        </Section>

        <Section heading="Exchanges">
          <Prose>
            <p>
              Wrong size is the usual one. Return it and order the right size —
              it&apos;s faster than a formal exchange and you&apos;re not waiting
              on our stock check.
            </p>
            <p>
              If the size you want has sold out in the meantime, tell us and
              we&apos;ll hold one from the next run.
            </p>
          </Prose>
        </Section>

        <Section heading="If something's wrong with it">
          <Prose>
            <p>
              Faulty print, dodgy stitching, wrong item in the bag — send a photo
              and we&apos;ll replace it, no return needed. That&apos;s our
              mistake, not your errand.
            </p>
            <p>
              This sits alongside your rights under Australian Consumer Law,
              which nothing here limits.
            </p>
          </Prose>
        </Section>

        <Section heading="What we can't take back">
          <Prose>
            <p>
              Worn or washed items, and anything returned after 30 days. Not
              because we&apos;re precious — we just can&apos;t resell it and
              won&apos;t pretend otherwise.
            </p>
          </Prose>
        </Section>
      </div>
    </PageShell>
  );
}
