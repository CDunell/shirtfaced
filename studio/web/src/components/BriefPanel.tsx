/**
 * The brief — what the product is, decided before any artwork exists.
 *
 * Phase 4 of DESIGN_FLOW_PLAN.md: the constitution's steps 1–4 and 6, which
 * had no representation in software at all. The 14 August audit's diagnosis of
 * why output arrived as competent generic work was that the research bench
 * produced a graphic idea and jumped straight to artwork, with no collection
 * role and no declared archetype.
 *
 * Two of these gate an attempt: collection role and graphic archetype. The rest
 * are the constitution's §3 required fields, saved as you go — a brief is
 * filled in over time, and refusing a half-written one would push the thinking
 * back out of the tool, which is where it was.
 *
 * **The advisor answers as you choose.** `design_advisor` recommends a scale
 * role and presentation from 12,151 measured images, and until Phase 4 nothing
 * called it. Its recommendation sits beside the choice, with its evidence and
 * its confidence, and going against it is recorded rather than prevented — the
 * corpus settles register, it does not set direction.
 */

import { useCallback, useEffect, useState } from "react";
import { useStyletron } from "baseui";
import { Button, KIND as BUTTON_KIND, SIZE } from "baseui/button";
import { FormControl } from "baseui/form-control";
import { Input } from "baseui/input";
import { Notification, KIND as NOTIFICATION_KIND } from "baseui/notification";
import { ParagraphSmall, ParagraphXSmall } from "baseui/typography";

import { ApiError } from "../api/client";
import {
  fetchAdvice,
  fetchBrief,
  saveBrief,
  type AdvisorDirection,
  type BriefView,
} from "../api/concepts";
import { SectionTitle } from "./chrome";
import { CORAL, INK, LIME, PAPER } from "../tokens";

function describe(cause: unknown): string {
  if (cause instanceof ApiError) return cause.message;
  return cause instanceof Error ? cause.message : String(cause);
}

/** Constitution §4. The five the constitution names, not domain.ts's six. */
const COLLECTION_ROLES: { id: string; label: string; blurb: string }[] = [
  { id: "anchor", label: "Anchor", blurb: "Carries recognition over time." },
  { id: "core", label: "Core", blurb: "Repeatable and commercially dependable." },
  { id: "expression", label: "Expression", blurb: "Seasonal, stronger graphic intensity." },
  { id: "hero", label: "Hero", blurb: "The principal statement of a drop." },
  { id: "collaboration", label: "Collaboration", blurb: "External IP or partner identity." },
];

/** Constitution §8 — one dominant graphic archetype per design. */
const GRAPHIC_ARCHETYPES: { id: string; label: string }[] = [
  { id: "image_led_hero", label: "Image-led hero" },
  { id: "typographic_hero", label: "Typographic hero" },
  { id: "emblem_or_badge", label: "Emblem or badge" },
  { id: "image_and_title_lockup", label: "Image-and-title lockup" },
  { id: "poster_or_editorial", label: "Poster or editorial panel" },
  { id: "symbolic_icon_system", label: "Symbolic icon system" },
  { id: "collage_controlled_frame", label: "Collage, controlled frame" },
  { id: "character_or_object_portrait", label: "Character or object portrait" },
  { id: "all_over_or_jumbo_field", label: "All-over or jumbo field" },
];

/** Constitution §6 — A1 to A8. */
const LAYOUT_ARCHETYPES: { id: string; label: string }[] = [
  { id: "a1_small_front_large_back", label: "A1 · Small front / large back" },
  { id: "a2_front_hero_rear_signature", label: "A2 · Front hero / rear signature" },
  { id: "a3_front_hero_clean_back", label: "A3 · Front hero / clean back" },
  { id: "a4_micro_front_back_hero", label: "A4 · Micro front / back hero" },
  { id: "a5_unequal_front_and_back", label: "A5 · Unequal front and back" },
  { id: "a6_image_language_split", label: "A6 · Image / language split" },
  { id: "a7_multi_zone", label: "A7 · Multi-zone system" },
  { id: "a8_jumbo_field", label: "A8 · Jumbo field" },
];

/** The §3 fields that are free text. Named explicitly rather than as
 * `keyof BriefView`, which also admits the JSONB objects and the booleans and
 * then needs a String() around every read to keep the compiler quiet. */
type ProductField =
  | "garment_category"
  | "canonical_blank"
  | "fit_block"
  | "fabric_weight"
  | "garment_colour"
  | "wash"
  | "production_method"
  | "commercial_tier"
  | "target_release";

/** Constitution §3's required product fields, in the order it lists them. */
const PRODUCT_FIELDS: { key: ProductField; label: string; placeholder: string }[] = [
  { key: "garment_category", label: "Garment category", placeholder: "tee, hoodie, cap" },
  { key: "canonical_blank", label: "Canonical blank", placeholder: "the actual blank" },
  { key: "fit_block", label: "Fit block", placeholder: "regular, oversized, crop" },
  { key: "fabric_weight", label: "Fabric weight", placeholder: "240gsm" },
  { key: "garment_colour", label: "Garment colour", placeholder: "black" },
  { key: "wash", label: "Wash or surface", placeholder: "none, garment-dyed" },
  { key: "production_method", label: "Production method", placeholder: "screen print" },
  { key: "commercial_tier", label: "Commercial tier", placeholder: "core, premium" },
  { key: "target_release", label: "Target release", placeholder: "drop or capsule" },
];

export interface BriefPanelProps {
  conceptId: string;
  conceptText: string;
  onChanged: () => Promise<void> | void;
}

export function BriefPanel({
  conceptId,
  conceptText,
  onChanged,
}: BriefPanelProps): React.JSX.Element {
  const [css, theme] = useStyletron();
  const [brief, setBrief] = useState<BriefView | null>(null);
  const [advice, setAdvice] = useState<AdvisorDirection | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    try {
      setBrief(await fetchBrief(conceptId));
    } catch (cause) {
      setError(describe(cause));
    }
  }, [conceptId]);

  useEffect(() => {
    const timer = setTimeout(() => {
      void load();
    }, 0);
    return () => {
      clearTimeout(timer);
    };
  }, [load]);

  // The advisor reads the concept's own words. It is asked once when the panel
  // opens rather than on every keystroke: it measures a corpus, not a form.
  useEffect(() => {
    const timer = setTimeout(() => {
      fetchAdvice(conceptText, true)
        .then(setAdvice)
        .catch(() => {
          // No advice is a state, not a failure. The brief is still fillable.
          setAdvice(null);
        });
    }, 0);
    return () => {
      clearTimeout(timer);
    };
  }, [conceptText]);

  const patch = useCallback(
    (changes: Partial<BriefView>) => {
      if (!brief) return;
      const next = { ...brief, ...changes };
      setBrief(next);
      setBusy(true);
      setError(null);
      saveBrief(conceptId, {
        ...next,
        // What the advisor said when this was chosen, kept so a decision can be
        // read back against the advice it was given — including where the owner
        // went the other way, which is the interesting case.
        advisor_snapshot: (advice ?? {}) as unknown as Record<string, unknown>,
      })
        .then((saved) => {
          setBrief(saved);
          return onChanged();
        })
        .catch((cause: unknown) => {
          setError(describe(cause));
        })
        .finally(() => {
          setBusy(false);
        });
    },
    [brief, conceptId, advice, onChanged],
  );

  const chip = (active: boolean, accent?: string) =>
    css({
      appearance: "none",
      border: "none",
      cursor: "pointer",
      fontFamily: "inherit",
      fontSize: "12px",
      fontWeight: 700,
      borderRadius: "999px",
      padding: "7px 13px",
      backgroundColor: active
        ? (accent ?? theme.colors.contentPrimary)
        : theme.colors.backgroundSecondary,
      color: active ? theme.colors.backgroundPrimary : theme.colors.contentSecondary,
      ":disabled": { cursor: "default", opacity: 0.6 },
    });

  const panel = css({
    border: `1px solid ${theme.colors.backgroundSecondary}`,
    borderRadius: "16px",
    padding: "16px",
    marginBottom: "16px",
  });

  if (!brief) {
    return (
      <ParagraphSmall color={theme.colors.contentSecondary}>Loading the brief…</ParagraphSmall>
    );
  }

  return (
    <div data-testid="brief-panel">
      <section
        className={css({
          backgroundColor: brief.ready_for_artwork ? theme.colors.backgroundSecondary : INK,
          color: brief.ready_for_artwork ? theme.colors.contentPrimary : PAPER,
          borderRadius: "16px",
          padding: "16px 18px",
          marginBottom: "16px",
        })}
      >
        <span
          className={css({
            display: "block",
            fontSize: "11px",
            fontWeight: 700,
            letterSpacing: "0.12em",
            textTransform: "uppercase",
            color: brief.ready_for_artwork ? theme.colors.contentTertiary : LIME,
            marginBottom: "6px",
          })}
        >
          {brief.ready_for_artwork ? "The product is defined" : "Before any artwork"}
        </span>
        <p className={css({ margin: 0, fontSize: "15px", lineHeight: 1.5 })}>{brief.next_action}</p>
      </section>

      {error ? (
        <Notification
          kind={NOTIFICATION_KIND.negative}
          overrides={{ Body: { style: { width: "auto" } } }}
        >
          {error}
        </Notification>
      ) : null}

      {advice ? (
        <div className={panel} data-testid="advisor">
          <SectionTitle>What the corpus says</SectionTitle>
          <ParagraphXSmall color={theme.colors.contentTertiary} marginTop={0}>
            Measured from the design corpus, offered as register rather than direction. Going
            against it is recorded, not prevented.
          </ParagraphXSmall>
          {advice.recommendations.map((item) => (
            <div
              key={item.field}
              className={css({
                borderTop: `1px solid ${theme.colors.backgroundSecondary}`,
                paddingTop: "8px",
                marginTop: "8px",
              })}
            >
              <ParagraphSmall marginTop={0} marginBottom="2px">
                <strong>{item.field.replace(/_/g, " ")}</strong> — {item.value.replace(/_/g, " ")}
              </ParagraphSmall>
              <ParagraphXSmall marginTop={0} marginBottom={0} color={theme.colors.contentTertiary}>
                {item.evidence} · {item.confidence}
              </ParagraphXSmall>
            </div>
          ))}
          {advice.not_decided.length > 0 ? (
            <ParagraphXSmall color={theme.colors.contentTertiary}>
              It will not say: {advice.not_decided.join(", ")}.
            </ParagraphXSmall>
          ) : null}
        </div>
      ) : null}

      {/* Step 2 — the role in the range. Gates an attempt. */}
      <div className={panel}>
        <SectionTitle>Role in the range</SectionTitle>
        <ParagraphXSmall color={theme.colors.contentTertiary} marginTop={0}>
          Constitution §4. A collection must not consist entirely of hero or expression products.
        </ParagraphXSmall>
        <div className={css({ display: "flex", gap: "6px", flexWrap: "wrap" })}>
          {COLLECTION_ROLES.map((role) => (
            <button
              key={role.id}
              type="button"
              disabled={busy}
              aria-pressed={brief.collection_role === role.id}
              aria-label={`Collection role: ${role.label}`}
              title={role.blurb}
              onClick={() => {
                patch({ collection_role: role.id });
              }}
              className={chip(brief.collection_role === role.id)}
            >
              {role.label}
            </button>
          ))}
        </div>
      </div>

      {/* Step 4 — the dominant graphic archetype. Gates an attempt. */}
      <div className={panel}>
        <SectionTitle>Graphic archetype</SectionTitle>
        <ParagraphXSmall color={theme.colors.contentTertiary} marginTop={0}>
          Constitution §8. One dominant archetype and one dominant proposition.
        </ParagraphXSmall>
        <div className={css({ display: "flex", gap: "6px", flexWrap: "wrap" })}>
          {GRAPHIC_ARCHETYPES.map((item) => (
            <button
              key={item.id}
              type="button"
              disabled={busy}
              aria-pressed={brief.graphic_archetype === item.id}
              aria-label={`Graphic archetype: ${item.label}`}
              onClick={() => {
                patch({ graphic_archetype: item.id });
              }}
              className={chip(brief.graphic_archetype === item.id)}
            >
              {item.label}
            </button>
          ))}
        </div>
      </div>

      {/* Step 3, partly — the layout archetype. Not gated: §6 allows a
          documented departure, so refusing to proceed without one would be
          stricter than the constitution. */}
      <div className={panel}>
        <SectionTitle>Layout archetype</SectionTitle>
        <ParagraphXSmall color={theme.colors.contentTertiary} marginTop={0}>
          Constitution §6. Departure from the library requires a written reason.
        </ParagraphXSmall>
        <div className={css({ display: "flex", gap: "6px", flexWrap: "wrap" })}>
          {LAYOUT_ARCHETYPES.map((item) => (
            <button
              key={item.id}
              type="button"
              disabled={busy}
              aria-pressed={brief.layout_archetype === item.id}
              aria-label={`Layout archetype: ${item.label}`}
              onClick={() => {
                patch({ layout_archetype: item.id });
              }}
              className={chip(brief.layout_archetype === item.id, CORAL)}
            >
              {item.label}
            </button>
          ))}
        </div>
      </div>

      {/* Step 1 — define the product. §3's required fields. */}
      <div className={panel}>
        <SectionTitle>The product</SectionTitle>
        <ParagraphXSmall color={theme.colors.contentTertiary} marginTop={0}>
          Constitution §3. Artwork created without a defined blank is exploratory only and cannot
          receive production approval.
        </ParagraphXSmall>
        <div
          className={css({
            display: "grid",
            gridTemplateColumns: "repeat(auto-fit, minmax(180px, 1fr))",
            gap: "10px",
          })}
        >
          {PRODUCT_FIELDS.map((field) => (
            <FormControl key={field.key} label={field.label}>
              <Input
                value={brief[field.key]}
                placeholder={field.placeholder}
                onChange={(event) => {
                  setBrief({ ...brief, [field.key]: event.currentTarget.value });
                }}
                onBlur={(event) => {
                  patch({ [field.key]: event.currentTarget.value });
                }}
              />
            </FormControl>
          ))}
        </div>
        <Button
          size={SIZE.compact}
          kind={BUTTON_KIND.secondary}
          disabled={busy}
          onClick={() => {
            patch({});
          }}
        >
          {busy ? "Saving…" : "Save the brief"}
        </Button>
      </div>
    </div>
  );
}
