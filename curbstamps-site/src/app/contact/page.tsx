import { PageShell, Section, Prose } from "@/components/PageShell";

export const metadata = { title: "Contact — Curb Stamps" };

export default function ContactPage() {
  return (
    <PageShell title="contact" intro="Order issues, wholesale, press — one address, real replies.">
      <Section heading="Email">
        <p className="text-[16px] font-bold">hello@curbstamps.com.au</p>
      </Section>
      <Section heading="Wholesale">
        <Prose>
          <p>Stock a shop or run a school fundraiser? Email us — we do small runs.</p>
        </Prose>
      </Section>
      <Section heading="Press">
        <Prose>
          <p>Same address. Tell us what you need and by when.</p>
        </Prose>
      </Section>
    </PageShell>
  );
}
