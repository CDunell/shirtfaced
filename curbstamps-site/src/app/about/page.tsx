import { PageShell, Prose, Section } from "@/components/PageShell";
import { CREATURES } from "@/lib/creatures";

export const metadata = { title: "About — My Mixups" };

export default function AboutPage() {
  return (
    <PageShell title="about" intro="A growing crew of weird little creatures made for kids to wear their favourite.">
      <Prose>
        <p>
          My Mixups started with a bunch of odd little creature doodles and kept growing.
          Some look almost familiar. Some definitely don&apos;t. Each one has its own shape,
          name and personality — and kids get to decide which one is theirs.
        </p>
        <p>
          The crew lives on tees, hoodies and caps made for everyday kid life: playgrounds,
          daycare, school, weekends, spills, dirt and whatever else happens before dinner.
        </p>
      </Prose>

      <Section heading="Made to be worn">
        <Prose>
          <p>
            The creatures are simple on purpose: bold, clean artwork that reads properly on
            a garment without turning kids&apos; clothes into a walking billboard. Good basics,
            good prints and weird little characters doing the heavy lifting.
          </p>
        </Prose>
      </Section>

      <Section heading="The crew keeps growing">
        <Prose>
          <p>
            New Mixups join the range as they&apos;re ready. What&apos;s live today:
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
          <p>
            My Mixups is an independent Australian kids&apos; label built around one simple idea:
            make fun clothes kids actually want to pick for themselves.
          </p>
        </Prose>
      </Section>
    </PageShell>
  );
}
