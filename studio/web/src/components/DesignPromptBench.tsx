import { useState } from "react";
import { Button, Checkbox, Notification, ParagraphSmall, ParagraphXSmall, Select, Textarea } from "./ui";

import { ApiError } from "../api/client";
import { fetchAdvice, fetchRandomConcept, retireConcept, type AdvisorDirection } from "../api/concepts";
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
  const [idea, setIdea] = useState("");
  const [hasGraphic, setHasGraphic] = useState(true);
  const [tradition, setTradition] = useState<string>("novelty");
  const [busy, setBusy] = useState(false);
  const [direction, setDirection] = useState<AdvisorDirection | null>(null);
  const [error, setError] = useState("");
  const [retired, setRetired] = useState(false);

  async function generate(): Promise<void> {
    if (!idea.trim()) return;
    setBusy(true);
    setError("");
    setRetired(false);
    try {
      const result = await fetchAdvice(idea, hasGraphic, tradition);
      setDirection(result);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Something went wrong.");
    } finally {
      setBusy(false);
    }
  }

  async function surpriseMe(): Promise<void> {
    setBusy(true);
    setError("");
    setRetired(false);
    try {
      const result = await fetchRandomConcept(tradition);
      setDirection(result);
    } catch (err) {
      if (err instanceof ApiError && err.status === 404) {
        setError(
          `No batch-written concepts for "${tradition}" yet -- this is a first pass covering ` +
            "a handful of traditions, not all of them. Type your own idea above instead.",
        );
      } else {
        setError(err instanceof Error ? err.message : "Something went wrong.");
      }
    } finally {
      setBusy(false);
    }
  }

  async function retireThis(): Promise<void> {
    if (!direction?.concept_id) return;
    setBusy(true);
    try {
      await retireConcept(direction.concept_id);
      setRetired(true);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Couldn't retire that one.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="max-w-[720px]">
      <PageTitle>Prompt</PageTitle>
      <ParagraphSmall className="text-ink/70">
        Describe the idea. This turns it into a paste-ready prompt for ChatGPT, Nano Banana
        or Grok, using what the corpus actually measures for that tradition — layout, ink
        count, placement, colourway. Nothing else. No brief, no queue, no review.
      </ParagraphSmall>

      <Textarea
        value={idea}
        onChange={(e) => setIdea(e.currentTarget.value)}
        placeholder="e.g. Enormous vintage maritime painting of a tiny speedboat vertical in a monstrous wave, SHE'LL BE RIGHT underneath"
        className="mt-4 min-h-20"
      />

      <div className="mt-3 flex flex-wrap items-center gap-4">
        <div className="min-w-[220px]">
          <Select
            options={TRADITIONS.map((t) => ({ value: t, label: t }))}
            value={tradition}
            onChange={setTradition}
          />
        </div>
        <Checkbox checked={hasGraphic} onChange={setHasGraphic}>
          Has a graphic (not text-only)
        </Checkbox>
        <Button
          size="compact"
          isLoading={busy}
          disabled={!idea.trim()}
          onClick={() => void generate()}
        >
          Generate prompt
        </Button>
        <Button size="compact" variant="secondary" isLoading={busy} onClick={() => void surpriseMe()}>
          Surprise me
        </Button>
      </div>
      <ParagraphXSmall className="mt-1.5 text-ink/70">
        No idea yet? "Surprise me" picks a batch-written concept for the selected tradition
        instead of one you type — real corpus grounding either way, just not your words.
      </ParagraphXSmall>

      {error ? (
        <Notification kind="negative" className="mt-4">
          {error}
        </Notification>
      ) : null}

      {direction ? (
        <div className="mt-6">
          <ParagraphXSmall className="mb-1.5 text-ink/70">
            {tradition} · {direction.recommendations.some((r) => r.confidence === "corpus")
              ? "evidence-backed"
              : "corpus has no data for this tradition — treat this as a default, not a measurement"}
          </ParagraphXSmall>
          <div className="rounded-lg border border-current p-4 leading-normal whitespace-pre-wrap">
            {direction.generation_prompt}
          </div>
          <div className="mt-2 flex items-center gap-3">
            <CopyButton text={direction.generation_prompt} label="Copy prompt" />
            {direction.concept_id && !retired ? (
              <Button size="compact" variant="ghost" isLoading={busy} onClick={() => void retireThis()}>
                Retire this one
              </Button>
            ) : null}
            {retired ? (
              <ParagraphXSmall className="text-ink/70">
                Retired — won't come up again from "Surprise me".
              </ParagraphXSmall>
            ) : null}
          </div>
        </div>
      ) : null}
    </div>
  );
}
