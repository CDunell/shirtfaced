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
import {
  Button,
  Card,
  cx,
  FormControl,
  Input,
  LabelSmall,
  Notification,
  ParagraphSmall,
  ParagraphXSmall,
  Select,
  Tag,
} from "./ui";

import { PageTitle, SectionTitle } from "./chrome";

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
  garment: string;
  placement: string;
  primary: string;
  secondary: string;
  garmentColour: string;
}

const INITIAL: Draft = {
  seed: 1,
  garment: "garment_tee_crew_front",
  placement: "centre_chest",
  primary: "SHIRTFACED",
  secondary: "",
  garmentColour: "#101010",
};

function briefOf(draft: Draft) {
  return {
    seed: draft.seed,
    garment_key: draft.garment,
    placement: draft.placement || "centre_chest",
    primary_text: draft.primary,
    secondary_text: draft.secondary,
    garment_colour: draft.garmentColour,
  };
}

export function ComposeBench(): React.JSX.Element {
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

  return (
    <>
      <PageTitle>Compose</PageTitle>
      <ParagraphSmall className="mt-0 text-ink/70">
        A garment, some words and a seed. The same four inputs always produce the same artwork, so a
        seed is worth writing down.
      </ParagraphSmall>

      {error ? <Notification kind="negative">{error}</Notification> : null}

      <Card className="mb-7">
        <div className="flex flex-wrap gap-3">
          <div className="flex-[1_1_180px] min-w-[160px]">
            <FormControl label="Garment">
              <Select
                options={GARMENTS.map((g) => ({ value: g, label: g.replace("garment_", "") }))}
                value={draft.garment}
                onChange={(value) => {
                  setDraft((d) => ({ ...d, garment: value }));
                }}
              />
            </FormControl>
          </div>
          <div className="flex-[1_1_180px] min-w-[160px]">
            <FormControl label="Placement">
              <Select
                options={PLACEMENTS.map((p) => ({ value: p, label: p }))}
                value={draft.placement}
                onChange={(value) => {
                  setDraft((d) => ({ ...d, placement: value }));
                }}
              />
            </FormControl>
          </div>
          <div className="flex-[1_1_180px] min-w-[160px]">
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

        <div className="mt-3 flex flex-wrap gap-3">
          <div className="flex-[1_1_180px] min-w-[160px]">
            <FormControl label="Words" caption="Never edited by the engine">
              <Input
                value={draft.primary}
                onChange={(event) => {
                  setDraft((d) => ({ ...d, primary: event.currentTarget.value }));
                }}
              />
            </FormControl>
          </div>
          <div className="flex-[1_1_180px] min-w-[160px]">
            <FormControl label="Second line" caption="Optional">
              <Input
                value={draft.secondary}
                onChange={(event) => {
                  setDraft((d) => ({ ...d, secondary: event.currentTarget.value }));
                }}
              />
            </FormControl>
          </div>
          <div className="flex-[1_1_180px] min-w-[160px]">
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

        <div className="mt-3 flex items-center gap-2">
          <Button
            size="compact"
            disabled={busy}
            onClick={() => {
              void onCompose();
            }}
          >
            {busy ? "Composing…" : "Compose"}
          </Button>
          <Button
            size="compact"
            variant="ghost"
            onClick={() => {
              setDraft((d) => ({ ...d, seed: d.seed + 1 }));
            }}
          >
            Next seed
          </Button>
        </div>
      </Card>

      {options && options.length === 0 ? (
        <Notification kind="warning">Nothing composed for this brief.</Notification>
      ) : null}

      {options && options.length > 0 ? (
        <div className="mb-9 grid grid-cols-[repeat(auto-fill,minmax(220px,1fr))] gap-3">
          {options.map((option) => (
            <Card key={option.content_hash}>
              <div
                className="mb-2 flex justify-center rounded-[6px] p-2.5"
                style={{ background: draft.garmentColour }}
                // The artwork is our own SVG from our own service, rendered so
                // it can be judged at a glance rather than described.
                dangerouslySetInnerHTML={{ __html: fitToCard(option.svg) }}
              />
              <LabelSmall>{option.grammar_name}</LabelSmall>
              <ParagraphXSmall className="mt-0 text-ink/70">{option.reads_as}</ParagraphXSmall>
              <div className="flex flex-wrap gap-1">
                <Tag kind="neutral">
                  {option.width_mm.toFixed(0)}×{option.height_mm.toFixed(0)}mm
                </Tag>
                <Tag kind="neutral">
                  {option.decisions === 0
                    ? "never decided"
                    : `${String(option.approvals)}/${String(option.decisions)} kept`}
                </Tag>
              </div>
              <ParagraphXSmall className="text-ink/70">{option.rationale}</ParagraphXSmall>
              <Button
                size="compact"
                variant="secondary"
                disabled={busy}
                onClick={() => {
                  void onKeep(option.grammar_key);
                }}
              >
                Keep
              </Button>
            </Card>
          ))}
        </div>
      ) : null}

      <SectionTitle>Kept</SectionTitle>
      <ParagraphSmall className="mt-0 text-ink/70">
        A kept design is not an approved one. Nothing leaves <code>awaiting_decision</code> without
        a name against it.
      </ParagraphSmall>

      <div className="mb-6 max-w-[280px]">
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
        <ParagraphSmall className="text-ink/70">Nothing kept yet.</ParagraphSmall>
      ) : (
        <div className="grid grid-cols-[repeat(auto-fill,minmax(220px,1fr))] gap-3">
          {kept.map((design) => {
            const check = checks[design.id];
            return (
              <Card key={design.id}>
                <div
                  className="mb-2 flex justify-center rounded-[6px] bg-[#101010] p-2.5"
                  dangerouslySetInnerHTML={{ __html: fitToCard(design.svg) }}
                />
                <div className="flex flex-wrap gap-1">
                  <Tag
                    kind={
                      design.state === "approved"
                        ? "positive"
                        : design.state === "rejected"
                          ? "negative"
                          : "warning"
                    }
                  >
                    {design.state.replace(/_/g, " ")}
                  </Tag>
                  <Tag kind="neutral">seed {design.seed}</Tag>
                </div>
                <ParagraphXSmall className="mt-0 text-ink/70">
                  {design.garment_key.replace("garment_", "")} · {design.placement_key} ·{" "}
                  {design.grammar_key}
                </ParagraphXSmall>

                {design.state === "awaiting_decision" ? (
                  <div className="flex gap-1.5">
                    <Button
                      size="compact"
                      disabled={busy}
                      onClick={() => {
                        void onDecide(design, true);
                      }}
                    >
                      Approve
                    </Button>
                    <Button
                      size="compact"
                      variant="secondary"
                      disabled={busy}
                      onClick={() => {
                        void onDecide(design, false);
                      }}
                    >
                      Reject
                    </Button>
                  </div>
                ) : (
                  <ParagraphXSmall className="mt-0">
                    {design.state} by {design.decided_by}
                  </ParagraphXSmall>
                )}

                <Button
                  size="compact"
                  variant="ghost"
                  onClick={() => {
                    void onVerify(design);
                  }}
                >
                  Rebuild from its brief
                </Button>
                {check ? (
                  <ParagraphXSmall className={cx("mt-0", check.reproducible ? "text-lime" : "text-coral")}>
                    {check.reproducible
                      ? "Rebuilt byte for byte."
                      : `Did not rebuild: ${check.reason ?? "bytes differ"}`}
                  </ParagraphXSmall>
                ) : null}
              </Card>
            );
          })}
        </div>
      )}
    </>
  );
}
