import { PageShell, Prose, Section } from "@/components/PageShell";
import { contact } from "@/lib/content-data.generated";

export const metadata = {
  title: "Contact — shirtfaced",
  description: "Talk to a human. Usually within one business day.",
};

export default function ContactPage() {
  return (
    <PageShell title="contact" intro={contact.intro}>
      <div className="flex flex-col gap-8">
        <Section heading="Email">
          <Prose>
            <p>
              <a
                href={`mailto:${contact.email}`}
                className="font-semibold underline underline-offset-4"
              >
                {contact.email}
              </a>
              {" — "}orders, returns, sizing, complaints, compliments.
            </p>
            <p>
              Include your order number if you have one. It saves an entire
              round trip.
            </p>
          </Prose>
        </Section>

        <Section heading="Wholesale &amp; stockists">
          <Prose>
            <p>{contact.wholesaleP1}</p>
          </Prose>
        </Section>

        <Section heading="Press &amp; collabs">
          <Prose>
            <p>{contact.pressP1}</p>
          </Prose>
        </Section>
      </div>

      <div className="mt-10 rounded-[20px] bg-ink px-6 py-6 text-paper">
        <p className="display text-[20px] leading-tight">{contact.bottomBlurb}</p>
      </div>
    </PageShell>
  );
}
