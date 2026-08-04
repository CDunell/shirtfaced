import { PageShell, Prose, Section } from "@/components/PageShell";
import { about } from "@/lib/content-data.generated";

export const metadata = {
  title: "About — Shirtfaced",
  description:
    "Graphic tees for people with questionable judgement and excellent taste. Designed in Australia.",
};

export default function AboutPage() {
  return (
    <PageShell title="about" intro={about.intro}>
      <div className="flex flex-col gap-8">
        <Section heading="The idea">
          <Prose>
            <p>{about.ideaP1}</p>
            <p>{about.ideaP2}</p>
          </Prose>
        </Section>

        <Section heading="How they're made">
          <Prose>
            <p>{about.howMadeP1}</p>
            <p>{about.howMadeP2}</p>
          </Prose>
        </Section>

        <Section heading="What we won't do">
          <Prose>
            <p>{about.wontDoP1}</p>
          </Prose>
        </Section>

        <Section heading="Who's behind it">
          <Prose>
            <p>{about.whoP1}</p>
          </Prose>
        </Section>
      </div>
    </PageShell>
  );
}
