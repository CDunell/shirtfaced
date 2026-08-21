import Link from "next/link";
import { PageShell, Prose, Section } from "@/components/PageShell";

export const metadata = {
  title: "Terms & conditions — shirtfaced",
  description: "The boring page. Read it once, then never think about it again.",
};

export default function TermsPage() {
  return (
    <PageShell
      title="terms"
      intro="The boring page. Read it once, then never think about it again."
    >
      <div className="flex flex-col gap-8">
        <Section heading="Using this site">
          <Prose>
            <p>
              Order something and you&apos;re agreeing to this. Standard
              stuff — nothing here is designed to catch you out, it mostly
              exists because a website with no terms page looks like
              it&apos;s hiding something.
            </p>
          </Prose>
        </Section>

        <Section heading="Prices">
          <Prose>
            <p>
              Everything&apos;s in Australian dollars, GST included where it
              applies. If a price is wrong — a typo, a decimal in the wrong
              place, a shirt listed at four dollars — we&apos;ll contact you
              before charging anything, and you can walk away with no hard
              feelings.
            </p>
          </Prose>
        </Section>

        <Section heading="Orders">
          <Prose>
            <p>
              An order&apos;s confirmed at checkout, not accepted until it
              ships. We can cancel one that looks like fraud, a stock error,
              or someone trying to buy the whole size run to resell at a
              markup. You&apos;ll get your money back either way, no
              argument.
            </p>
          </Prose>
        </Section>

        <Section heading="Shipping & returns">
          <Prose>
            <p>
              Covered properly on the <Link href="/shipping" className="underline underline-offset-2">shipping</Link> and{" "}
              <Link href="/returns" className="underline underline-offset-2">returns</Link>{" "}
              pages. Not repeating it here — you can read the same sentence twice
              somewhere that isn&apos;t this one.
            </p>
          </Prose>
        </Section>

        <Section heading="Designs & the name">
          <Prose>
            <p>
              The designs, the name and the logo are ours. Buy the shirt,
              wear the shirt, don&apos;t lift the artwork and print it
              yourself — that&apos;s the one thing we&apos;ll actually get
              precious about.
            </p>
          </Prose>
        </Section>

        <Section heading="Liability">
          <Prose>
            <p>
              We&apos;re liable for what we&apos;re liable for under
              Australian Consumer Law, and nothing on this page tries to
              wriggle out of that. Beyond those guarantees, we&apos;re not
              on the hook for what happens after you put the shirt on —
              that part&apos;s between you and your choices.
            </p>
          </Prose>
        </Section>

        <Section heading="Changes">
          <Prose>
            <p>
              We can update these terms. The version that applies is
              whichever one was live on the site when you ordered.
            </p>
          </Prose>
        </Section>

        <Section heading="Questions">
          <Prose>
            <p>hello@shirtfaced.wtf, same as everything else.</p>
          </Prose>
        </Section>
      </div>
    </PageShell>
  );
}
