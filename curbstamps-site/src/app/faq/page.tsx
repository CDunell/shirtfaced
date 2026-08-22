import { PageShell } from "@/components/PageShell";
import { FaqAccordion, type FaqItem } from "./FaqAccordion";

export const metadata = { title: "FAQ — Curb Stamps" };

const FAQ: FaqItem[] = [
  {
    question: "What sizes do you carry?",
    answer:
      "One size chart across the whole range: toddler 2T–5T, then youth XS through XL (roughly ages 6 to teen). Caps come in Toddler or Youth.",
    linkHref: "/size-guide",
    linkLabel: "See the size guide",
  },
  {
    question: "How are the designs printed?",
    answer: "Screen-printed line art, not vinyl or a heat-press sticker. It's made to survive the wash and the yard.",
  },
  {
    question: "How long does an order take?",
    answer: "Each order is printed to order once it comes in, then shipped standard (3–7 business days) or express (1–3 business days).",
    linkHref: "/shipping",
    linkLabel: "Shipping details",
  },
  {
    question: "Can I return or exchange something?",
    answer: "Yes — unworn, unwashed items within 30 days.",
    linkHref: "/returns",
    linkLabel: "Returns policy",
  },
  {
    question: "Is it just 12 creatures?",
    answer: "For now — 60 are planned, and new ones ship as the art's finished, not on a fixed schedule.",
  },
  {
    question: "Where do I go if something's wrong with an order?",
    answer: "Get in touch and we'll sort it.",
    linkHref: "/contact",
    linkLabel: "Contact us",
  },
];

export default function FaqPage() {
  return (
    <PageShell title="faq" intro="The questions that come up before the ones that come up after.">
      <FaqAccordion items={FAQ} />
    </PageShell>
  );
}
