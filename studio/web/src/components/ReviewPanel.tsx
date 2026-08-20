/**
 * The automated review of one image.
 *
 * A recommendation, never a decision. Failed and uncertain gates are expanded first,
 * because those are what the owner needs to look at.
 */

import { LabelXSmall, Notification, ParagraphSmall, ParagraphXSmall, Tag, type TagKind } from "./ui";

import type { GateName, GateResult, GateStatus, Review, ReviewRecommendation } from "../api/client";

const RECOMMENDATION_LABELS: Record<ReviewRecommendation, string> = {
  APPROVE_RECOMMENDED: "Approval recommended",
  APPROVE_WITH_NOTE_RECOMMENDED: "Approval with a note recommended",
  REJECT_RECOMMENDED: "Rejection recommended",
  REVIEW_UNCERTAIN: "Uncertain — needs your eyes",
};

const RECOMMENDATION_KINDS: Record<ReviewRecommendation, TagKind> = {
  APPROVE_RECOMMENDED: "positive",
  APPROVE_WITH_NOTE_RECOMMENDED: "warning",
  REJECT_RECOMMENDED: "negative",
  REVIEW_UNCERTAIN: "accent",
};

const GATE_LABELS: Record<GateName, string> = {
  mood: "Mood",
  australian_authenticity: "Australian authenticity",
  product_visibility: "Product visibility",
  third_party_branding: "Third-party branding",
  vehicle_continuity: "Vehicle continuity",
  wardrobe_balance: "Wardrobe balance",
  composition: "Composition",
  documentary_credibility: "Documentary credibility",
  story: "Story",
};

const GATE_ORDER: GateName[] = [
  "mood",
  "australian_authenticity",
  "product_visibility",
  "third_party_branding",
  "vehicle_continuity",
  "wardrobe_balance",
  "composition",
  "documentary_credibility",
  "story",
];

const STATUS_KINDS: Record<GateStatus, TagKind> = {
  PASS: "positive",
  FAIL: "negative",
  UNCERTAIN: "warning",
  NOT_APPLICABLE: "neutral",
};

const STATUS_LABELS: Record<GateStatus, string> = {
  PASS: "Pass",
  FAIL: "Fail",
  UNCERTAIN: "Uncertain",
  NOT_APPLICABLE: "Not applicable",
};

function GateRow({ name, gate }: { name: GateName; gate: GateResult }): React.JSX.Element {
  return (
    <div className="grid gap-2 border-b border-ink/10 py-4">
      <div className="flex flex-wrap items-center gap-3">
        <LabelXSmall>{GATE_LABELS[name]}</LabelXSmall>
        <Tag kind={STATUS_KINDS[gate.status]}>{STATUS_LABELS[gate.status]}</Tag>
        {gate.material && gate.status === "FAIL" && <Tag kind="negative">Material</Tag>}
        <ParagraphXSmall className="text-ink/50">
          confidence {gate.confidence.toFixed(2)}
        </ParagraphXSmall>
      </div>

      <ParagraphXSmall className="text-ink/70">{gate.evidence}</ParagraphXSmall>

      {gate.codes.length > 0 && (
        <div className="flex flex-wrap gap-1">
          {gate.codes.map((code) => (
            <Tag key={code} kind="neutral">
              {code}
            </Tag>
          ))}
        </div>
      )}
    </div>
  );
}

export function ReviewPanel({ review }: { review: Review }): React.JSX.Element {
  const attention = new Set<GateName>([...review.blocking_gates, ...review.uncertain_gates]);
  // Failed and uncertain gates first; the rest keep the contract's declared order.
  const ordered = [
    ...GATE_ORDER.filter((name) => attention.has(name)),
    ...GATE_ORDER.filter((name) => !attention.has(name)),
  ];

  const scores: [string, number][] = [
    ["Mood", review.mood_score],
    ["Australian authenticity", review.australian_authenticity_score],
    ["Product visibility", review.product_visibility_score],
    ["Documentary credibility", review.documentary_credibility_score],
    ["Story", review.story_score],
  ];

  return (
    <div className="mt-6">
      <div className="flex flex-wrap items-center gap-3">
        <Tag kind={RECOMMENDATION_KINDS[review.recommendation]}>
          {RECOMMENDATION_LABELS[review.recommendation]}
        </Tag>
        <ParagraphXSmall className="text-ink/50">This is advice. You decide.</ParagraphXSmall>
      </div>

      <ParagraphSmall>{review.strongest_success}</ParagraphSmall>

      {review.material_drift && (
        <div className="mt-4">
          <Notification kind="warning">{review.material_drift}</Notification>
        </div>
      )}

      <div className="mt-5 flex flex-wrap gap-2">
        {scores.map(([label, score]) => (
          <Tag key={label} kind="neutral">
            {`${label} ${String(score)}/5`}
          </Tag>
        ))}
        <Tag kind={review.branding_compliant ? "positive" : "negative"}>
          {review.branding_compliant ? "Branding compliant" : "Branding breach"}
        </Tag>
        <Tag kind={review.vehicle_compliant ? "positive" : "negative"}>
          {review.vehicle_compliant ? "Vehicle compliant" : "Vehicle breach"}
        </Tag>
      </div>

      <details open={attention.size > 0} className="mt-5">
        <summary className="cursor-pointer text-[11px] font-semibold tracking-wide uppercase text-ink/60">
          {attention.size > 0
            ? `${String(attention.size)} gate${attention.size === 1 ? "" : "s"} need attention`
            : "All nine gates"}
        </summary>
        <div className="mt-3">
          {ordered.map((name) => (
            <GateRow key={name} name={name} gate={review.gates[name]} />
          ))}
        </div>
      </details>

      {review.next_hero_product && (
        <ParagraphXSmall className="text-ink/50">
          Suggested next: {review.next_hero_product}
          {review.next_camera ? ` — ${review.next_camera}` : ""}
        </ParagraphXSmall>
      )}
    </div>
  );
}
