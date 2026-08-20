import { PageShell, Prose, Section } from "@/components/PageShell";
import { garmentCare } from "@/lib/content-data.generated";

export const metadata = {
  title: "Garment care — shirtfaced",
  description: "How to wash it without wrecking it.",
};

export default function GarmentCarePage() {
  return (
    <PageShell title="garment care" intro={garmentCare.intro}>
      <div className="flex flex-col gap-8">
        <Section heading="Washing">
          <Prose>
            <p>{garmentCare.washingP1}</p>
          </Prose>
        </Section>

        <Section heading="Drying">
          <Prose>
            <p>{garmentCare.dryingP1}</p>
          </Prose>
        </Section>

        <Section heading="Print care">
          <Prose>
            <p>{garmentCare.printCareP1}</p>
          </Prose>
        </Section>

        <Section heading="Storage">
          <Prose>
            <p>{garmentCare.storageP1}</p>
          </Prose>
        </Section>
      </div>
    </PageShell>
  );
}
