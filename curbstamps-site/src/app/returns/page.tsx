import { PageShell, Section, Prose } from "@/components/PageShell";

export const metadata = { title: "Returns — Curb Stamps" };

export default function ReturnsPage() {
  return (
    <PageShell title="returns" intro="Unworn, unwashed, within 30 days — no drama.">
      <Section heading="How it works">
        <ol className="mt-1 flex flex-col gap-4">
          {[
            ["Get in touch", "Email us with your order number and what's wrong."],
            ["We'll send a label", "Post it back — we cover return shipping on our mistakes, not on a change of mind."],
            ["We check it", "Unworn, unwashed, tags on."],
            ["Refund or exchange", "Your call — money back or a straight swap for a different size or creature."],
          ].map(([title, body]) => (
            <li key={title}>
              <p className="text-[15px] font-bold">{title}</p>
              <p className="text-[14px] text-grey-dark">{body}</p>
            </li>
          ))}
        </ol>
      </Section>
      <Section heading="Exchanges">
        <Prose>
          <p>Sizes runs true, but kids grow mid-shipment — swap for a size up or down within 30 days, no cost either way.</p>
        </Prose>
      </Section>
      <Section heading="Wrong or faulty item">
        <Prose>
          <p>If we got it wrong or the print&apos;s faulty, tell us and we&apos;ll fix it — replacement or refund, our cost.</p>
        </Prose>
      </Section>
      <Section heading="What we can't take back">
        <Prose>
          <p>Anything worn, washed, or without its original tags.</p>
        </Prose>
      </Section>
    </PageShell>
  );
}
