import { PageShell } from "@/components/PageShell";
import { faq } from "@/lib/content-data.generated";
import { FaqAccordion } from "./FaqAccordion";

export const metadata = {
  title: "FAQ — shirtfaced",
  description: "The questions that come up before the ones that come up after.",
};

export default function FaqPage() {
  return (
    <PageShell title="faq" intro={faq.intro}>
      <FaqAccordion items={faq.items} />
    </PageShell>
  );
}
