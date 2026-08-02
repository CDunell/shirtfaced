import { PageShell, Prose, Section } from "@/components/PageShell";

export const metadata = {
  title: "Contact — Shirtfaced",
  description: "Talk to a human. Usually within one business day.",
};

export default function ContactPage() {
  return (
    <PageShell
      title="contact"
      intro="A real person reads these, usually within one business day. Weekends are a gamble."
    >
      <div className="flex flex-col gap-8">
        <Section heading="Email">
          <Prose>
            <p>
              <a
                href="mailto:hello@shirtfaced.wtf"
                className="font-semibold underline underline-offset-4"
              >
                hello@shirtfaced.wtf
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
            <p>
              If you run a shop and want these on a rack, email the same address
              with &ldquo;wholesale&rdquo; in the subject and we&apos;ll send a
              line sheet.
            </p>
          </Prose>
        </Section>

        <Section heading="Press &amp; collabs">
          <Prose>
            <p>
              Also the same address. We&apos;re not big enough for separate
              inboxes and pretending otherwise would be embarrassing.
            </p>
          </Prose>
        </Section>
      </div>

      <div className="mt-10 rounded-[20px] bg-ink px-6 py-6 text-paper">
        <p className="display text-[20px] leading-tight">
          nice shirt. shame about your choices.
        </p>
      </div>
    </PageShell>
  );
}
