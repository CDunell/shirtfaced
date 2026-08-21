import { PageShell, Prose, Section } from "@/components/PageShell";

export const metadata = {
  title: "Privacy — shirtfaced",
  description: "What we collect, why, and the short list of things we won't do with it.",
};

export default function PrivacyPage() {
  return (
    <PageShell
      title="privacy"
      intro="What we collect, why, and the short list of things we're not going to do with it."
    >
      <div className="flex flex-col gap-8">
        <Section heading="What we collect">
          <Prose>
            <p>
              Name, delivery address, email, and whatever you tell us in a
              support message. Your order history — what you bought, when,
              and how many times you&apos;ve bought the same shirt for
              different mates. Standard site stuff too: browser, device, the
              pages you looked at before you committed. None of this is
              unusual. Every site collects it. We&apos;re just not going to
              be weird about it.
            </p>
          </Prose>
        </Section>

        <Section heading="What we don't do">
          <Prose>
            <p>
              We don&apos;t sell your details. Not to advertisers, not to
              &quot;partners,&quot; not to anyone. We&apos;re not building a
              list to flog later — the whole company is a handful of people
              and a printer, we wouldn&apos;t know who to sell it to.
            </p>
          </Prose>
        </Section>

        <Section heading="Who else sees it">
          <Prose>
            <p>
              The payment processor, to take your money properly. The
              courier, to find your house. The email platform, if you signed
              up for the newsletter and haven&apos;t got around to
              unsubscribing. Google, Meta and TikTok get a slice too — see
              Cookies below — strictly to tell us whether an ad worked, not
              a bonus copy of your details for anyone&apos;s own purposes.
            </p>
          </Prose>
        </Section>

        <Section heading="Cookies">
          <Prose>
            <p>
              The cart remembers what&apos;s in it, which needs a cookie. We
              also run analytics (Google Analytics) so we know which pages
              people actually read — this one, hopefully — plus Meta and
              TikTok pixels, so if we run an ad we can tell whether it
              actually sold a shirt instead of just guessing. If you come
              in from one of those ads, that platform knows you looked. We
              use that to see what&apos;s working, not to build a profile on
              you or follow you around the rest of the internet — turn the
              relevant setting off in your Google, Meta or TikTok account if
              you&apos;d rather opt out of that measurement entirely.
            </p>
          </Prose>
        </Section>

        <Section heading="Your rights">
          <Prose>
            <p>
              Under the Privacy Act 1988 (Cth), you can ask what we hold on
              you, ask us to fix it, or ask us to delete it. Email us and
              we&apos;ll sort it out — no form, no ticket number, no
              three-week hold music.
            </p>
            <p>
              The entity actually responsible for your data is BM Media
              (ABN 34 538 203 506), trading as shirtfaced.
            </p>
          </Prose>
        </Section>

        <Section heading="If this changes">
          <Prose>
            <p>
              We&apos;ll update this page and it&apos;ll say what it says.
              We&apos;re not going to email you a modal about it.
            </p>
          </Prose>
        </Section>

        <Section heading="Questions">
          <Prose>
            <p>hello@shirtfaced.wtf. A real person reads it.</p>
          </Prose>
        </Section>
      </div>
    </PageShell>
  );
}
