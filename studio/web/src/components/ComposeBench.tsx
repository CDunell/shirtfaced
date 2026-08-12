/**
 * Driving the composer.
 *
 * The archive has held elements, grammars, garments and placements for weeks
 * with no way to see what any of it makes. This is that: give it a garment, some
 * words and a seed, and look at what comes back.
 *
 * Three states, deliberately separate. Composing shows options and keeps
 * nothing. Keeping stores one and leaves it undecided. Deciding is the only way
 * out of `awaiting_decision`, and it asks who is deciding, because an approval
 * nobody signed is not an approval.
 *
 * The seed is on screen rather than hidden, because it is the whole contract:
 * the same seed, garment, words and palette must produce the same bytes, and
 * somebody has to be able to type last month's seed back in and check.
 */

import { useCallback, useEffect, useState } from "react";
import { useStyletron } from "baseui";
import { Button, KIND as BUTTON_KIND, SIZE } from "baseui/button";
import { Card, StyledBody } from "baseui/card";
import { FormControl } from "baseui/form-control";
import { Input } from "baseui/input";
import { Notification, KIND as NOTIFICATION_KIND } from "baseui/notification";
import { Select, type Value } from "baseui/select";
import { Tag, KIND as TAG_KIND } from "baseui/tag";
import { HeadingSmall, LabelSmall, ParagraphSmall, ParagraphXSmall } from "baseui/typography";

import {
  ApiError,
  composeDesign,
  decideDesign,
  keepDesign,
  listDesigns,
  verifyDesign,
  type ComposedOption,
  type Reproducibility,
  type StoredDesign,
} from "../api/client";
import { fitToCard } from "./svg";

function describe(cause: unknown): string {
  if (cause instanceof ApiError) return cause.message;
  return cause instanceof Error ? cause.message : String(cause);
}

/** Every garment file in assets/garments, by stem. */
const GARMENTS = [
  "garment_tee_crew_front",
  "garment_tee_crew_back",
  "garment_tee_oversized_front",
  "garment_tee_oversized_back",
  "garment_tee_vneck_front",
  "garment_tee_vneck_back",
  "garment_tee_longsleeve_front",
  "garment_tee_longsleeve_back",
  "garment_crop_front",
  "garment_crop_back",
  "garment_tank_muscle_front",
  "garment_tank_muscle_back",
  "garment_beanie_front",
  "garment_beanie_back",
  "garment_bucket_hat_front",
  "garment_bucket_hat_back",
  "garment_cap_dad_front",
  "garment_cap_dad_back",
  "garment_cap_snapback_front",
  "garment_cap_snapback_back",
  "garment_cap_trucker_front",
  "garment_cap_trucker_back",
];

const PLACEMENTS = [
  "centre_chest",
  "left_chest",
  "full_front",
  "full_back",
  "upper_back_yoke",
  "centre_back",
  "outer_back_neck",
  "short_sleeve",
  "long_sleeve",
  "pocket",
  "cap_front",
  "cap_side",
  "cap_back",
];

/** A brief with a seed the owner can see, change and come back to. */
interface Draft {
  seed: number;
  garment: Value;
  placement: Value;
  primary: string;
  secondary: string;
  garmentColour: string;
}

const INITIAL: Draft = {
  seed: 1,
  garment: [{ id: "garment_tee_crew_front", label: "garment_tee_crew_front" }],
  placement: [{ id: "centre_chest", label: "centre_chest" }],
  primary: "SHIRTFACED",
  secondary: "",
  garmentColour: "#101010",
};

function briefOf(draft: Draft) {
  return {
    seed: draft.seed,
    garment_key: String(draft.garment[0]?.id ?? ""),
    placement: String(draft.placement[0]?.id ?? "centre_chest"),
    primary_text: draft.primary,
    secondary_text: draft.secondary,
    garment_colour: draft.garmentColour,
  };
}

export function ComposeBench(): React.JSX.Element {
  const [css, theme] = useStyletron();
  const [draft, setDraft] = useState<Draft>(INITIAL);
  const [options, setOptions] = useState<ComposedOption[] | null>(null);
  const [kept, setKept] = useState<StoredDesign[]>([]);
  const [decider, setDecider] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [checks, setChecks] = useState<Record<string, Reproducibility>>({});

  const refresh = useCallback(async () => {
    try {
      setKept(await listDesigns());
    } catch (cause) {
      setError(describe(cause));
    }
  }, []);

  useEffect(() => {
    // One load on mount. The kept list is server state, so it is fetched rather
    // than derived, and nothing here depends on the composing form.
    const timer = setTimeout(() => {
      void refresh();
    }, 0);
    return () => {
      clearTimeout(timer);
    };
  }, [refresh]);

  const onCompose = useCallback(async () => {
    setBusy(true);
    setError(null);
    setOptions(null);
    try {
      setOptions(await composeDesign(briefOf(draft)));
    } catch (cause) {
      setError(describe(cause));
    } finally {
      setBusy(false);
    }
  }, [draft]);

  const onKeep = useCallback(
    async (grammarKey: string) => {
      setBusy(true);
      setError(null);
      try {
        await keepDesign(briefOf(draft), grammarKey);
        await refresh();
      } catch (cause) {
        setError(describe(cause));
      } finally {
        setBusy(false);
      }
    },
    [draft, refresh],
  );

  const onDecide = useCallback(
    async (design: StoredDesign, approved: boolean) => {
      if (!decider.trim()) {
        setError("A decision needs a name against it.");
        return;
      }
      setBusy(true);
      setError(null);
      try {
        await decideDesign(design.id, approved, decider.trim());
        await refresh();
      } catch (cause) {
        setError(describe(cause));
      } finally {
        setBusy(false);
      }
    },
    [decider, refresh],
  );

  const onVerify = useCallback(async (design: StoredDesign) => {
    try {
      const result = await verifyDesign(design.id);
      setChecks((old) => ({ ...old, [design.id]: result }));
    } catch (cause) {
      setError(describe(cause));
    }
  }, []);

  const field = css({ flex: "1 1 180px", minWidth: "160px" });

  return (
    <>
      <HeadingSmall marginTop={0} marginBottom={theme.sizing.scale300}>
        Compose
      </HeadingSmall>
      <ParagraphSmall color={theme.colors.contentSecondary} marginTop={0}>
        A garment, some words and a seed. The same four inputs always produce the same artwork, so a
        seed is worth writing down.
      </ParagraphSmall>

      {error ? (
        <Notification
          kind={NOTIFICATION_KIND.negative}
          overrides={{ Body: { style: { width: "auto" } } }}
        >
          {error}
        </Notification>
      ) : null}

      <Card overrides={{ Root: { style: { marginBottom: theme.sizing.scale700 } } }}>
        <StyledBody>
          <div className={css({ display: "flex", flexWrap: "wrap", gap: "12px" })}>
            <div className={field}>
              <FormControl label="Garment">
                <Select
                  clearable={false}
                  searchable
                  options={GARMENTS.map((g) => ({ id: g, label: g.replace("garment_", "") }))}
                  value={draft.garment}
                  onChange={({ value }) => {
                    setDraft((d) => ({ ...d, garment: value }));
                  }}
                />
              </FormControl>
            </div>
            <div className={field}>
              <FormControl label="Placement">
                <Select
                  clearable={false}
                  searchable
                  options={PLACEMENTS.map((p) => ({ id: p, label: p }))}
                  value={draft.placement}
                  onChange={({ value }) => {
                    setDraft((d) => ({ ...d, placement: value }));
                  }}
                />
              </FormControl>
            </div>
            <div className={field}>
              <FormControl label="Seed" caption="Same seed, same design">
                <Input
                  type="number"
                  min={0}
                  value={String(draft.seed)}
                  onChange={(event) => {
                    setDraft((d) => ({
                      ...d,
                      seed: Math.max(0, Number(event.currentTarget.value)),
                    }));
                  }}
                />
              </FormControl>
            </div>
          </div>

          <div className={css({ display: "flex", flexWrap: "wrap", gap: "12px" })}>
            <div className={field}>
              <FormControl label="Words" caption="Never edited by the engine">
                <Input
                  value={draft.primary}
                  onChange={(event) => {
                    setDraft((d) => ({ ...d, primary: event.currentTarget.value }));
                  }}
                />
              </FormControl>
            </div>
            <div className={field}>
              <FormControl label="Second line" caption="Optional">
                <Input
                  value={draft.secondary}
                  onChange={(event) => {
                    setDraft((d) => ({ ...d, secondary: event.currentTarget.value }));
                  }}
                />
              </FormControl>
            </div>
            <div className={field}>
              <FormControl label="Garment colour">
                <Input
                  value={draft.garmentColour}
                  onChange={(event) => {
                    setDraft((d) => ({ ...d, garmentColour: event.currentTarget.value }));
                  }}
                />
              </FormControl>
            </div>
          </div>

          <div className={css({ display: "flex", gap: "8px", alignItems: "center" })}>
            <Button
              size={SIZE.compact}
              isLoading={busy}
              onClick={() => {
                void onCompose();
              }}
            >
              Compose
            </Button>
            <Button
              size={SIZE.compact}
              kind={BUTTON_KIND.tertiary}
              onClick={() => {
                setDraft((d) => ({ ...d, seed: d.seed + 1 }));
              }}
            >
              Next seed
            </Button>
          </div>
        </StyledBody>
      </Card>

      {options && options.length === 0 ? (
        <Notification kind={NOTIFICATION_KIND.warning}>
          Nothing composed for this brief.
        </Notification>
      ) : null}

      {options && options.length > 0 ? (
        <div
          className={css({
            display: "grid",
            gridTemplateColumns: "repeat(auto-fill, minmax(220px, 1fr))",
            gap: "12px",
            marginBottom: theme.sizing.scale900,
          })}
        >
          {options.map((option) => (
            <Card key={option.content_hash}>
              <StyledBody>
                <div
                  className={css({
                    background: draft.garmentColour,
                    borderRadius: "6px",
                    padding: "10px",
                    marginBottom: "8px",
                    display: "flex",
                    justifyContent: "center",
                  })}
                  // The artwork is our own SVG from our own service, rendered so
                  // it can be judged at a glance rather than described.
                  dangerouslySetInnerHTML={{ __html: fitToCard(option.svg) }}
                />
                <LabelSmall>{option.grammar_name}</LabelSmall>
                <ParagraphXSmall color={theme.colors.contentSecondary} marginTop={0}>
                  {option.reads_as}
                </ParagraphXSmall>
                <div className={css({ display: "flex", gap: "4px", flexWrap: "wrap" })}>
                  <Tag closeable={false} kind={TAG_KIND.neutral}>
                    {option.width_mm.toFixed(0)}×{option.height_mm.toFixed(0)}mm
                  </Tag>
                  <Tag closeable={false} kind={TAG_KIND.neutral}>
                    {option.decisions === 0
                      ? "never decided"
                      : `${String(option.approvals)}/${String(option.decisions)} kept`}
                  </Tag>
                </div>
                <ParagraphXSmall color={theme.colors.contentSecondary}>
                  {option.rationale}
                </ParagraphXSmall>
                <Button
                  size={SIZE.mini}
                  kind={BUTTON_KIND.secondary}
                  disabled={busy}
                  onClick={() => {
                    void onKeep(option.grammar_key);
                  }}
                >
                  Keep
                </Button>
              </StyledBody>
            </Card>
          ))}
        </div>
      ) : null}

      <HeadingSmall marginBottom={theme.sizing.scale300}>Kept</HeadingSmall>
      <ParagraphSmall color={theme.colors.contentSecondary} marginTop={0}>
        A kept design is not an approved one. Nothing leaves <code>awaiting_decision</code> without
        a name against it.
      </ParagraphSmall>

      <div className={css({ maxWidth: "280px", marginBottom: theme.sizing.scale600 })}>
        <FormControl label="Deciding as">
          <Input
            value={decider}
            placeholder="your name"
            onChange={(event) => {
              setDecider(event.currentTarget.value);
            }}
          />
        </FormControl>
      </div>

      {kept.length === 0 ? (
        <ParagraphSmall color={theme.colors.contentSecondary}>Nothing kept yet.</ParagraphSmall>
      ) : (
        <div
          className={css({
            display: "grid",
            gridTemplateColumns: "repeat(auto-fill, minmax(220px, 1fr))",
            gap: "12px",
          })}
        >
          {kept.map((design) => {
            const check = checks[design.id];
            return (
              <Card key={design.id}>
                <StyledBody>
                  <div
                    className={css({
                      background: "#101010",
                      borderRadius: "6px",
                      padding: "10px",
                      marginBottom: "8px",
                      display: "flex",
                      justifyContent: "center",
                    })}
                    dangerouslySetInnerHTML={{ __html: fitToCard(design.svg) }}
                  />
                  <div className={css({ display: "flex", gap: "4px", flexWrap: "wrap" })}>
                    <Tag
                      closeable={false}
                      kind={
                        design.state === "approved"
                          ? TAG_KIND.positive
                          : design.state === "rejected"
                            ? TAG_KIND.negative
                            : TAG_KIND.warning
                      }
                    >
                      {design.state.replace(/_/g, " ")}
                    </Tag>
                    <Tag closeable={false} kind={TAG_KIND.neutral}>
                      seed {design.seed}
                    </Tag>
                  </div>
                  <ParagraphXSmall color={theme.colors.contentSecondary} marginTop={0}>
                    {design.garment_key.replace("garment_", "")} · {design.placement_key} ·{" "}
                    {design.grammar_key}
                  </ParagraphXSmall>

                  {design.state === "awaiting_decision" ? (
                    <div className={css({ display: "flex", gap: "6px" })}>
                      <Button
                        size={SIZE.mini}
                        disabled={busy}
                        onClick={() => {
                          void onDecide(design, true);
                        }}
                      >
                        Approve
                      </Button>
                      <Button
                        size={SIZE.mini}
                        kind={BUTTON_KIND.secondary}
                        disabled={busy}
                        onClick={() => {
                          void onDecide(design, false);
                        }}
                      >
                        Reject
                      </Button>
                    </div>
                  ) : (
                    <ParagraphXSmall marginTop={0}>
                      {design.state} by {design.decided_by}
                    </ParagraphXSmall>
                  )}

                  <Button
                    size={SIZE.mini}
                    kind={BUTTON_KIND.tertiary}
                    onClick={() => {
                      void onVerify(design);
                    }}
                  >
                    Rebuild from its brief
                  </Button>
                  {check ? (
                    <ParagraphXSmall
                      marginTop={0}
                      color={check.reproducible ? theme.colors.positive : theme.colors.negative}
                    >
                      {check.reproducible
                        ? "Rebuilt byte for byte."
                        : `Did not rebuild: ${check.reason ?? "bytes differ"}`}
                    </ParagraphXSmall>
                  ) : null}
                </StyledBody>
              </Card>
            );
          })}
        </div>
      )}
    </>
  );
}
