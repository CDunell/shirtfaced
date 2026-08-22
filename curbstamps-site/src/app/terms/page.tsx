import { PageShell, Section, Prose } from "@/components/PageShell";

export const metadata = { title: "Terms — Curb Stamps" };

export default function TermsPage() {
  return (
    <PageShell title="terms" intro="The standard stuff, in plain language.">
      <div className="mb-6 rounded-2xl border-2 border-dashed border-ink/20 px-4 py-3 text-[13px] text-grey-dark">
        Placeholder terms — a working draft, not legal advice. Have a solicitor review
        this against the Australian Consumer Law before it goes live for real orders.
      </div>
      <Section heading="Using this site">
        <Prose>
          <p>By ordering from Curb Stamps you agree to these terms. We can update them — the current version always applies.</p>
        </Prose>
      </Section>
      <Section heading="Orders and pricing">
        <Prose>
          <p>Prices are in AUD and include GST. We&apos;ll tell you before charging you if something&apos;s changed since you added it to your cart.</p>
        </Prose>
      </Section>
      <Section heading="Your consumer guarantees">
        <Prose>
          <p>
            Nothing here limits your rights under the Australian Consumer Law — goods
            come with guarantees that can&apos;t be excluded, including a right to a refund,
            replacement or repair for a major failure.
          </p>
        </Prose>
      </Section>
      <Section heading="Intellectual property">
        <Prose>
          <p>The creatures, names and artwork are Curb Stamps&apos; own. Buying a tee doesn&apos;t buy the design.</p>
        </Prose>
      </Section>
    </PageShell>
  );
}
