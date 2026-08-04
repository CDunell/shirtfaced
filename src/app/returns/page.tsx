import { PageShell, Prose, Section } from "@/components/PageShell";
import { returns } from "@/lib/content-data.generated";

export const metadata = {
  title: "Returns — Shirtfaced",
  description: "30 days, unworn, no interrogation.",
};

const STEPS: [string, string][] = [
  [returns.step1Title, returns.step1Body],
  [returns.step2Title, returns.step2Body],
  [returns.step3Title, returns.step3Body],
  [returns.step4Title, returns.step4Body],
];

export default function ReturnsPage() {
  return (
    <PageShell title="returns" intro={returns.intro}>
      <div className="flex flex-col gap-8">
        <Section heading="How it works">
          <ol className="flex flex-col gap-4">
            {STEPS.map(([a, b], i) => (
              <li key={a} className="flex gap-4">
                <span className="display grid h-9 w-9 shrink-0 place-items-center rounded-full bg-ink text-[16px] text-paper">
                  {i + 1}
                </span>
                <span className="pt-1 text-[16px] leading-relaxed">
                  <strong>{a}</strong>
                  <br />
                  <span className="text-ink/70">{b}</span>
                </span>
              </li>
            ))}
          </ol>
        </Section>

        <Section heading="Exchanges">
          <Prose>
            <p>{returns.exchangesP1}</p>
            <p>{returns.exchangesP2}</p>
          </Prose>
        </Section>

        <Section heading="If something's wrong with it">
          <Prose>
            <p>{returns.wrongP1}</p>
            <p>{returns.wrongP2}</p>
          </Prose>
        </Section>

        <Section heading="What we can't take back">
          <Prose>
            <p>{returns.cantTakeP1}</p>
          </Prose>
        </Section>
      </div>
    </PageShell>
  );
}
