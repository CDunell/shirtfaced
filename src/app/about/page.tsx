import { PageShell, Prose, Section } from "@/components/PageShell";

export const metadata = {
  title: "About — Shirtfaced",
  description:
    "Graphic tees for people with questionable judgement and excellent taste. Designed in Australia.",
};

export default function AboutPage() {
  return (
    <PageShell
      title="about"
      intro="Shirtfaced makes graphic tees for people with questionable judgement and excellent taste. That's the entire brief."
    >
      <div className="flex flex-col gap-8">
        <Section heading="The idea">
          <Prose>
            <p>
              Most graphic tees are either forgettable or trying far too hard.
              We wanted the ones you actually reach for — heavy cotton, cut
              wide, printed with something worth reading from across a room.
            </p>
            <p>
              Every design starts as a joke someone refused to let go of. If it
              still lands a month later, it gets printed.
            </p>
          </Prose>
        </Section>

        <Section heading="How they're made">
          <Prose>
            <p>
              240gsm combed cotton, garment-dyed, boxy fit with a dropped
              shoulder. Screen-printed in Australia in small runs — not because
              scarcity is a marketing tactic, but because we&apos;d rather sell
              out than warehouse a thousand of something nobody wanted.
            </p>
            <p>
              Prints are built to crack and fade the way a good tee should. It
              will look better in a year than it does in the bag.
            </p>
          </Prose>
        </Section>

        <Section heading="What we won't do">
          <Prose>
            <p>
              No dropshipping. No print-on-demand from a warehouse we&apos;ve
              never seen. No countdown timers telling you four people are
              looking at this right now.
            </p>
          </Prose>
        </Section>

        <Section heading="Who's behind it">
          <Prose>
            <p>
              A small Australian outfit that started in 2026 and has so far made
              exactly the decisions you&apos;d expect from people who named a
              company this.
            </p>
          </Prose>
        </Section>
      </div>
    </PageShell>
  );
}
