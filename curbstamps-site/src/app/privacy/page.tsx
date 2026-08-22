import { PageShell, Section, Prose } from "@/components/PageShell";

export const metadata = { title: "Privacy — Curb Stamps" };

export default function PrivacyPage() {
  return (
    <PageShell title="privacy" intro="What we collect, and what we don't.">
      <div className="mb-6 rounded-2xl border-2 border-dashed border-ink/20 px-4 py-3 text-[13px] text-grey-dark">
        Placeholder privacy policy — a working draft, not legal advice. Review against
        the Australian Privacy Principles (and note this site collects children&apos;s
        clothing sizes, not children&apos;s own data) before it goes live for real orders.
      </div>
      <Section heading="What we collect">
        <Prose>
          <p>
            Name, email and delivery address to fulfil an order; payment details go
            straight to Stripe and never touch our own servers. Orders are placed by a
            parent or guardian — we don&apos;t knowingly collect information from children
            directly.
          </p>
        </Prose>
      </Section>
      <Section heading="Who we share it with">
        <Prose>
          <p>Our payment processor (Stripe) and our print-on-demand partner, to the extent needed to make and ship your order. No one else.</p>
        </Prose>
      </Section>
      <Section heading="Your rights">
        <Prose>
          <p>Ask us to see, correct or delete what we hold on you, any time.</p>
        </Prose>
      </Section>
    </PageShell>
  );
}
