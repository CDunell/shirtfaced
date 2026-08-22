import { PageShell, Prose, Section } from "@/components/PageShell";
import { CREATURES } from "@/lib/creatures";

export const metadata = { title: "About — Curb Stamps" };

export default function AboutPage() {
  return (
    <PageShell title="about" intro="Little creatures, found on the curb, stamped on your kid.">
      <Prose>
        <p>
          Curb Stamps started as a bunch of doodles of the little things you actually see on
          a footpath — bugs, bandicoots, the odd unexplainable devil — and turned into a
          collection of 60 characters, one at a time. Twelve are out in the world so far.
        </p>
        <p>
          Every creature gets a tee, a hoodie and a cap, sized from 2T right through to a
          teen&apos;s XL, so a kid can wear the same little guy from toddler years to
          actual-opinions-about-clothes years.
        </p>
      </Prose>

      <Section heading="How it's made">
        <Prose>
          <p>
            Every print is screen-printed, not vinyl, not a heat-press sticker that cracks
            after three washes. Thick ink, one line-art colour, made to survive a kid — and
            to get handed down to the next one.
          </p>
        </Prose>
      </Section>

      <Section heading="The crew, one at a time">
        <Prose>
          <p>
            New creatures ship as the art&apos;s finished, not on a schedule. What&apos;s live
            today:
          </p>
        </Prose>
        <ul className="mt-3 grid grid-cols-2 gap-x-4 gap-y-1 text-[14px] font-bold sm:grid-cols-3">
          {CREATURES.map((c) => (
            <li key={c.slug}>{c.name}</li>
          ))}
        </ul>
      </Section>

      <Section heading="Who's behind it">
        <Prose>
          <p>Curb Stamps is a small, independent kids&apos; label. No factory minimums we can&apos;t meet honestly, no drop we can&apos;t actually fulfil.</p>
        </Prose>
      </Section>
    </PageShell>
  );
}
