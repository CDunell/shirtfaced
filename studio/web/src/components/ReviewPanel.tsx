/**
 * The automated review of one image.
 *
 * A recommendation, never a decision. Failed and uncertain gates are expanded first,
 * because those are what the owner needs to look at.
 */

import { useStyletron } from "baseui";
import { Notification, KIND as NOTIFICATION_KIND } from "baseui/notification";
import { Tag, HIERARCHY, KIND as TAG_KIND, type TagKind } from "baseui/tag";
import { LabelXSmall, ParagraphSmall, ParagraphXSmall } from "baseui/typography";

import type { GateName, GateResult, GateStatus, Review, ReviewRecommendation } from "../api/client";

const RECOMMENDATION_LABELS: Record<ReviewRecommendation, string> = {
  APPROVE_RECOMMENDED: "Approval recommended",
  APPROVE_WITH_NOTE_RECOMMENDED: "Approval with a note recommended",
  REJECT_RECOMMENDED: "Rejection recommended",
  REVIEW_UNCERTAIN: "Uncertain — needs your eyes",
};

const RECOMMENDATION_KINDS: Record<ReviewRecommendation, TagKind> = {
  APPROVE_RECOMMENDED: TAG_KIND.positive,
  APPROVE_WITH_NOTE_RECOMMENDED: TAG_KIND.warning,
  REJECT_RECOMMENDED: TAG_KIND.negative,
  REVIEW_UNCERTAIN: TAG_KIND.accent,
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
  PASS: TAG_KIND.positive,
  FAIL: TAG_KIND.negative,
  UNCERTAIN: TAG_KIND.warning,
  NOT_APPLICABLE: TAG_KIND.neutral,
};

const STATUS_LABELS: Record<GateStatus, string> = {
  PASS: "Pass",
  FAIL: "Fail",
  UNCERTAIN: "Uncertain",
  NOT_APPLICABLE: "Not applicable",
};

function GateRow({ name, gate }: { name: GateName; gate: GateResult }): React.JSX.Element {
  const [css, theme] = useStyletron();

  return (
    <div
      className={css({
        display: "grid",
        gap: theme.sizing.scale200,
        paddingTop: theme.sizing.scale400,
        paddingBottom: theme.sizing.scale400,
        borderBottomWidth: "1px",
        borderBottomStyle: "solid",
        borderBottomColor: theme.colors.borderOpaque,
      })}
    >
      <div
        className={css({
          display: "flex",
          alignItems: "center",
          gap: theme.sizing.scale300,
          flexWrap: "wrap",
        })}
      >
        <LabelXSmall>{GATE_LABELS[name]}</LabelXSmall>
        <Tag closeable={false} kind={STATUS_KINDS[gate.status]} hierarchy={HIERARCHY.secondary}>
          {STATUS_LABELS[gate.status]}
        </Tag>
        {gate.material && gate.status === "FAIL" && (
          <Tag closeable={false} kind={TAG_KIND.negative} hierarchy={HIERARCHY.primary}>
            Material
          </Tag>
        )}
        <ParagraphXSmall marginTop={0} marginBottom={0} color={theme.colors.contentTertiary}>
          confidence {gate.confidence.toFixed(2)}
        </ParagraphXSmall>
      </div>

      <ParagraphXSmall marginTop={0} marginBottom={0} color={theme.colors.contentSecondary}>
        {gate.evidence}
      </ParagraphXSmall>

      {gate.codes.length > 0 && (
        <div className={css({ display: "flex", flexWrap: "wrap", gap: theme.sizing.scale100 })}>
          {gate.codes.map((code) => (
            <Tag
              key={code}
              closeable={false}
              kind={TAG_KIND.neutral}
              hierarchy={HIERARCHY.secondary}
            >
              {code}
            </Tag>
          ))}
        </div>
      )}
    </div>
  );
}

export function ReviewPanel({ review }: { review: Review }): React.JSX.Element {
  const [css, theme] = useStyletron();

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
    <div className={css({ marginTop: theme.sizing.scale600 })}>
      <div
        className={css({
          display: "flex",
          alignItems: "center",
          gap: theme.sizing.scale300,
          flexWrap: "wrap",
        })}
      >
        <Tag
          closeable={false}
          kind={RECOMMENDATION_KINDS[review.recommendation]}
          hierarchy={HIERARCHY.primary}
        >
          {RECOMMENDATION_LABELS[review.recommendation]}
        </Tag>
        <ParagraphXSmall marginTop={0} marginBottom={0} color={theme.colors.contentTertiary}>
          This is advice. You decide.
        </ParagraphXSmall>
      </div>

      <ParagraphSmall marginBottom={0}>{review.strongest_success}</ParagraphSmall>

      {review.material_drift && (
        <div className={css({ marginTop: theme.sizing.scale400 })}>
          <Notification
            kind={NOTIFICATION_KIND.warning}
            overrides={{ Body: { style: { width: "auto" } } }}
          >
            {review.material_drift}
          </Notification>
        </div>
      )}

      <div
        className={css({
          display: "flex",
          flexWrap: "wrap",
          gap: theme.sizing.scale200,
          marginTop: theme.sizing.scale500,
        })}
      >
        {scores.map(([label, score]) => (
          <Tag
            key={label}
            closeable={false}
            kind={TAG_KIND.neutral}
            hierarchy={HIERARCHY.secondary}
          >
            {`${label} ${String(score)}/5`}
          </Tag>
        ))}
        <Tag
          closeable={false}
          kind={review.branding_compliant ? TAG_KIND.positive : TAG_KIND.negative}
          hierarchy={HIERARCHY.secondary}
        >
          {review.branding_compliant ? "Branding compliant" : "Branding breach"}
        </Tag>
        <Tag
          closeable={false}
          kind={review.vehicle_compliant ? TAG_KIND.positive : TAG_KIND.negative}
          hierarchy={HIERARCHY.secondary}
        >
          {review.vehicle_compliant ? "Vehicle compliant" : "Vehicle breach"}
        </Tag>
      </div>

      <details open={attention.size > 0} className={css({ marginTop: theme.sizing.scale500 })}>
        <summary className={css({ ...theme.typography.LabelXSmall, cursor: "pointer" })}>
          {attention.size > 0
            ? `${String(attention.size)} gate${attention.size === 1 ? "" : "s"} need attention`
            : "All nine gates"}
        </summary>
        <div className={css({ marginTop: theme.sizing.scale300 })}>
          {ordered.map((name) => (
            <GateRow key={name} name={name} gate={review.gates[name]} />
          ))}
        </div>
      </details>

      {review.next_hero_product && (
        <ParagraphXSmall color={theme.colors.contentTertiary}>
          Suggested next: {review.next_hero_product}
          {review.next_camera ? ` — ${review.next_camera}` : ""}
        </ParagraphXSmall>
      )}
    </div>
  );
}
