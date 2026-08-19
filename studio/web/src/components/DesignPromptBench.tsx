import { useState } from "react";
import { Button, SIZE } from "baseui/button";
import { Textarea } from "baseui/textarea";
import { Select } from "baseui/select";
import { Checkbox } from "baseui/checkbox";
import { Notification, KIND as NOTIFICATION_KIND } from "baseui/notification";
import { ParagraphSmall, ParagraphXSmall } from "baseui/typography";
import { useStyletron } from "baseui";

import { fetchAdvice, type AdvisorDirection } from "../api/concepts";
import { CopyButton, PageTitle } from "./chrome";

const TRADITIONS = [
  "novelty",
  "streetwear",
  "skate",
  "outdoor",
  "surf",
  "band-merch",
  "veteran",
  "moto",
  "au-surf",
  "americana",
  "fishing",
  "golf",
  "varsity",
  "major-surf",
  "au-streetwear",
  "festival",
  "art-merch",
  "alt-horror",
  "esports",
  "counterculture",
  "cause",
  "creator-merch",
  "au-beer",
  "au-basics",
  "au-sport",
  "workwear",
  "fitness",
  "barber",
  "running",
  "au-western",
  "au-alt",
  "tattoo",
];

export function DesignPromptBench(): React.JSX.Element {
  const [css] = useStyletron();
  const [idea, setIdea] = useState("");
  const [hasGraphic, setHasGraphic] = useState(true);
  const [tradition, setTradition] = useState<{ id: string; label: string }>({
    id: "novelty",
    label: "novelty",
  });
  const [busy, setBusy] = useState(false);
  const [direction, setDirection] = useState<AdvisorDirection | null>(null);
  const [error, setError] = useState("");

  async function generate(): Promise<void> {
    if (!idea.trim()) return;
    setBusy(true);
    setError("");
    try {
      const result = await fetchAdvice(idea, hasGraphic, tradition.id);
      setDirection(result);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Something went wrong.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className={css({ maxWidth: "720px" })}>
      <PageTitle>Prompt</PageTitle>
      <ParagraphSmall marginTop={0} color="mono600">
        Describe the idea. This turns it into a paste-ready prompt for ChatGPT, Nano Banana
        or Grok, using what the corpus actually measures for that tradition — layout, ink
        count, placement, colourway. Nothing else. No brief, no queue, no review.
      </ParagraphSmall>

      <Textarea
        value={idea}
        onChange={(e) => setIdea(e.currentTarget.value)}
        placeholder="e.g. Enormous vintage maritime painting of a tiny speedboat vertical in a monstrous wave, SHE'LL BE RIGHT underneath"
        overrides={{
          Root: { style: { marginTop: "16px" } },
          Input: { style: { minHeight: "80px" } },
        }}
      />

      <div
        className={css({
          display: "flex",
          gap: "16px",
          alignItems: "center",
          marginTop: "12px",
          flexWrap: "wrap",
        })}
      >
        <div className={css({ minWidth: "220px" })}>
          <Select
            options={TRADITIONS.map((t) => ({ id: t, label: t }))}
            value={[tradition]}
            onChange={({ value }) => {
              const picked = value[0];
              if (picked) setTradition({ id: String(picked.id), label: String(picked.label) });
            }}
            clearable={false}
            searchable
            size={SIZE.compact}
          />
        </div>
        <Checkbox checked={hasGraphic} onChange={(e) => setHasGraphic(e.currentTarget.checked)}>
          Has a graphic (not text-only)
        </Checkbox>
        <Button
          size={SIZE.compact}
          isLoading={busy}
          disabled={!idea.trim()}
          onClick={() => void generate()}
        >
          Generate prompt
        </Button>
      </div>

      {error ? (
        <Notification kind={NOTIFICATION_KIND.negative} overrides={{ Body: { style: { marginTop: "16px" } } }}>
          {error}
        </Notification>
      ) : null}

      {direction ? (
        <div className={css({ marginTop: "24px" })}>
          <ParagraphXSmall color="mono600" marginBottom="6px">
            {tradition.id} · {direction.recommendations.some((r) => r.confidence === "corpus")
              ? "evidence-backed"
              : "corpus has no data for this tradition — treat this as a default, not a measurement"}
          </ParagraphXSmall>
          <div
            className={css({
              padding: "16px",
              border: "1px solid currentColor",
              borderRadius: "8px",
              whiteSpace: "pre-wrap",
              lineHeight: "1.5",
            })}
          >
            {direction.generation_prompt}
          </div>
          <CopyButton text={direction.generation_prompt} label="Copy prompt" />
        </div>
      ) : null}
    </div>
  );
}
