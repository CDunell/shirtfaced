import { PageShell, Prose, Section } from "@/components/PageShell";

export const metadata = {
  title: "Returns — shirtfaced",
  description: "Change of mind? Yeah nah. If we fucked it up, we'll fix it.",
};

export default function ReturnsPage() {
  return (
    <PageShell
      title="returns & other regrettable decisions"
      intro="You bought it. You picked the size. We made it. Everyone played their part."
    >
      <div className="flex flex-col gap-8">
        <Section heading="Changed your mind?">
          <Prose>
            <p>Yeah nah.</p>
            <p>
              We don&apos;t accept returns or exchanges because you changed your mind,
              ordered the wrong size, decided black isn&apos;t your colour, sobered up,
              or your mate said something unhelpful.
            </p>
            <p>
              Check the size guide before ordering. Measure a shirt you already own
              if you&apos;re not sure. It&apos;s considerably less annoying than discovering
              you&apos;re actually an XL through the postal system.
            </p>
          </Prose>
        </Section>

        <Section heading="Ordered the wrong size?">
          <Prose>
            <p>That&apos;s yours now.</p>
            <p>
              We make and fulfil our gear in small runs, so we don&apos;t operate a
              revolving door of size exchanges.
            </p>
            <p>Check twice. Order once.</p>
          </Prose>
        </Section>

        <Section heading="We fucked it up?">
          <Prose>
            <p>Different story.</p>
            <p>
              If we send you the wrong item, wrong size, or there&apos;s a genuine
              manufacturing or print fault, that&apos;s on us. Send us a photo and your
              order details and we&apos;ll sort it.
            </p>
            <p>No interpretive dance required.</p>
          </Prose>
        </Section>

        <Section heading="Your shirt has been through some shit">
          <Prose>
            <p>
              Once it&apos;s been worn, washed, stained, stretched, shrunk in a dryer hot
              enough to re-enter the atmosphere, attacked by a dog, left at a
              festival, or otherwise subjected to your lifestyle choices, we can&apos;t
              take it back for change of mind.
            </p>
            <p>Follow the care instructions. Or don&apos;t. We&apos;re a clothing company, not the police.</p>
          </Prose>
        </Section>

        <Section heading="Australian Consumer Law">
          <Prose>
            <p>
              None of the nonsense above takes away your rights under Australian
              Consumer Law. If something has a genuine fault, isn&apos;t what we said it
              was, or otherwise fails a consumer guarantee, you&apos;re entitled to the
              remedies provided by Australian Consumer Law.
            </p>
            <p>We&apos;ll honour those rights. Obviously.</p>
          </Prose>
        </Section>

        <Section heading="The short version">
          <Prose>
            <p><strong>Change of mind?</strong> No.</p>
            <p><strong>Wrong size because you ordered the wrong size?</strong> No.</p>
            <p><strong>Want to swap it for something else?</strong> No.</p>
            <p><strong>We sent the wrong thing?</strong> We&apos;ll fix it.</p>
            <p><strong>Genuine fault?</strong> We&apos;ll fix it.</p>
            <p><strong>Destroyed it yourself?</strong> Nice one.</p>
          </Prose>
        </Section>
      </div>
    </PageShell>
  );
}
