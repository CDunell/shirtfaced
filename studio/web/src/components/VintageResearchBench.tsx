/**
 * Two-pass design research over the vintage evidence.
 *
 * Pass one reads the selected listing photography and returns ten concepts;
 * pass two deepens each without changing what it is. The service does both in
 * one call, so a run is slow -- real image bytes go to the model twice -- and
 * the button says so rather than looking hung.
 *
 * Reviewing is the point of the screen. A concept can be approved, rejected,
 * edited, and once approved sent into the design pipeline against a chosen
 * concept number. Nothing here decides whether a design is good; it records
 * what a person decided, which is the same rule the rest of Studio follows.
 */

import { useCallback, useEffect, useState } from "react";

import {
  Button,
  Input,
  LabelSmall,
  Notification,
  ParagraphXSmall,
  Select,
  Tag,
  Textarea,
  type SelectOption,
  type TagKind,
} from "./ui";

import { CopyButton, PasteButton, PageTitle } from "./chrome";

import {
  ApiError,
  downloadResearchBundle,
  importManualRun,
  prepareManualRun,
  fetchDesignConceptTargets,
  fetchEvidence,
  fetchResearchRun,
  fetchResearchRuns,
  sendConceptToPipeline,
  startResearchRun,
  updateResearchConcept,
  type DesignConceptTarget,
  type EvidenceRecord,
  type ManualPrepared,
  type PipelineResult,
  type ResearchConcept,
  type ResearchRun,
} from "../api/client";

function statusKind(status: string | undefined): TagKind {
  if (status === "approved") return "positive";
  if (status === "rejected") return "negative";
  return "neutral";
}

const card = "mb-3 rounded-[10px] border border-ink/10 p-3";

/** Where a research concept landed, and what to do about it.
 *
 * A click that reports nothing is a click somebody repeats. This says which
 * numbered concept now exists and carries the server's own next-action
 * sentence, so the reader is not left to go and find out. */
function Landed({ result }: { result: PipelineResult | undefined }): React.JSX.Element | null {
  if (!result) return null;
  return (
    <ParagraphXSmall className="m-0 basis-full text-ink/70">
      {result.concept_created ? "Created " : "Added to "}#{String(result.design_concept_number)}{" "}
      {result.design_concept_title}
      {result.attempt_number !== null ? `, attempt ${String(result.attempt_number)}` : ""}.{" "}
      {result.next_action}
    </ParagraphXSmall>
  );
}

export function VintageResearchBench(): React.JSX.Element {
  const [runs, setRuns] = useState<ResearchRun[]>([]);
  const [run, setRun] = useState<ResearchRun | null>(null);
  const [targets, setTargets] = useState<DesignConceptTarget[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [query, setQuery] = useState("");
  // Era and tradition are picked, never typed. filter_evidence matches them by
  // exact equality, so a typed "90s" or "1990" returns nothing and says nothing
  // about why. The options carry their counts for the same reason the Evidence
  // bench does: the filter can state what it will return before it is chosen.
  const [era, setEra] = useState("");
  const [tradition, setTradition] = useState("");
  const [records, setRecords] = useState<EvidenceRecord[]>([]);
  const [imageLimit, setImageLimit] = useState("16");
  const [drafts, setDrafts] = useState<Record<number, string>>({});
  const [pipelineTarget, setPipelineTarget] = useState("");
  // Attempt number per concept, so the button reports what it created
  // rather than leaving a click with nothing to show for it. Null means the
  // concept was created or updated but no attempt could open yet -- see
  // Landed and the tag below, which both read that as "no attempt" rather
  // than printing the literal null.
  const [queued, setQueued] = useState<Record<number, number | null>>({});
  // Where each research concept landed, so the bench can say what happened and
  // what to do about it rather than leaving the reader to go and look.
  const [landed, setLanded] = useState<Record<number, PipelineResult>>({});
  // The manual path: prepare hands over the prompt and the images, you run both
  // passes in a subscription UI, then paste the JSON back. No metered API call
  // on either side of it.
  const [prepared, setPrepared] = useState<ManualPrepared | null>(null);
  const [pasted, setPasted] = useState("");

  useEffect(() => {
    const controller = new AbortController();
    void Promise.all([
      fetchResearchRuns(controller.signal),
      fetchDesignConceptTargets(controller.signal),
      fetchEvidence(controller.signal),
    ])
      .then(([loadedRuns, loadedTargets, evidence]) => {
        setRuns(loadedRuns);
        setTargets(loadedTargets);
        setRecords(evidence.records);
        if (loadedRuns.length > 0 && loadedRuns[0]) setRun(loadedRuns[0]);
      })
      .catch((cause: unknown) => {
        if (controller.signal.aborted) return;
        setError(cause instanceof ApiError ? cause.message : "Research runs unavailable.");
      });
    return () => {
      controller.abort();
    };
  }, []);

  const optionsFor = useCallback(
    (key: "era_claim" | "tradition"): SelectOption[] => {
      const counts = new Map<string, number>();
      for (const record of records) {
        const value = (record[key] ?? "").trim();
        if (value) counts.set(value, (counts.get(value) ?? 0) + 1);
      }
      return [...counts.entries()]
        .sort((a, b) => b[1] - a[1] || a[0].localeCompare(b[0]))
        .map(([id, n]) => ({ value: id, label: `${id} (${String(n)})` }));
    },
    [records],
  );

  const start = useCallback(() => {
    setBusy(true);
    setError(null);
    const limit = Number.parseInt(imageLimit, 10);
    startResearchRun({
      query,
      era,
      tradition,
      image_limit: Number.isFinite(limit) ? limit : 16,
    })
      .then((created) => {
        setRun(created);
        setRuns((previous) => [created, ...previous]);
        setBusy(false);
      })
      .catch((cause: unknown) => {
        setError(cause instanceof ApiError ? cause.message : "The research run failed.");
        setBusy(false);
      });
  }, [query, era, tradition, imageLimit]);

  const prepare = useCallback(() => {
    setError(null);
    const limit = Number.parseInt(imageLimit, 10);
    prepareManualRun({
      query,
      era,
      tradition,
      image_limit: Number.isFinite(limit) ? limit : 16,
    })
      .then((result) => {
        setPrepared(result);
      })
      .catch((cause: unknown) => {
        setError(cause instanceof ApiError ? cause.message : "Could not select evidence.");
      });
  }, [query, era, tradition, imageLimit]);

  const downloadBundle = useCallback(() => {
    setError(null);
    const limit = Number.parseInt(imageLimit, 10);
    downloadResearchBundle({
      query,
      era,
      tradition,
      image_limit: Number.isFinite(limit) ? limit : 16,
    })
      .then((blob) => {
        // Object URL rather than a data URI: a few megabytes of zip in a URI
        // is a string the browser has to hold twice.
        const url = URL.createObjectURL(blob);
        const link = document.createElement("a");
        link.href = url;
        link.download = "vintage-research-run.zip";
        link.click();
        URL.revokeObjectURL(url);
      })
      .catch((cause: unknown) => {
        setError(cause instanceof ApiError ? cause.message : "The bundle could not be built.");
      });
  }, [query, era, tradition, imageLimit]);

  const importPasted = useCallback(() => {
    setError(null);
    if (pasted.trim().length === 0) {
      setError(
        "Nothing in the box yet. Paste the JSON in, or use Paste JSON — if that " +
          "says Blocked, the browser refused clipboard access and you will need " +
          "to paste by hand.",
      );
      return;
    }
    let concepts: unknown[];
    try {
      const parsed: unknown = JSON.parse(pasted);
      concepts = Array.isArray(parsed)
        ? parsed
        : ((parsed as { concepts?: unknown[] }).concepts ?? []);
    } catch {
      setError("That is not valid JSON.");
      return;
    }
    importManualRun(concepts, prepared)
      .then((created) => {
        setRun(created);
        setRuns((previous) => [created, ...previous]);
        setPasted("");
        setPrepared(null);
      })
      .catch((cause: unknown) => {
        setError(cause instanceof ApiError ? cause.message : "Those concepts were refused.");
      });
  }, [pasted, prepared]);

  const applyConcept = useCallback(
    (number: number, body: { status?: string; prompt?: string }) => {
      if (!run) return;
      const runId = run.id;
      updateResearchConcept(runId, number, body)
        .then(() => fetchResearchRun(runId))
        .then((fresh) => {
          setRun(fresh);
        })
        .catch((cause: unknown) => {
          setError(cause instanceof ApiError ? cause.message : "That change did not save.");
        });
    },
    [run],
  );

  /** Send an approved research concept into the design pipeline.
   *
   * With a target, it becomes another attempt on an idea that already exists.
   * Without one it becomes a *new* numbered design concept -- the path that
   * did not exist before Phase 1, when the backlog was only reachable through
   * concept_importer reading a Markdown file and ten researched concepts could
   * not become ten backlog concepts.
   */
  const toPipeline = useCallback(
    (number: number, createNew: boolean) => {
      const target = pipelineTarget;
      if (!run) return;
      if (!createNew && target === "") return;
      sendConceptToPipeline(run.id, number, createNew ? null : target)
        .then((result) => {
          setError(null);
          setQueued((previous) => ({ ...previous, [number]: result.attempt_number }));
          setLanded((previous) => ({ ...previous, [number]: result }));
        })
        .catch((cause: unknown) => {
          setError(cause instanceof ApiError ? cause.message : "Could not queue that concept.");
        });
    },
    [run, pipelineTarget],
  );

  return (
    <>
      <PageTitle meta={run?.id ? `Run ${run.id.slice(0, 8)}` : `${String(runs.length)} runs`}>
        Vintage Research
      </PageTitle>
      <ParagraphXSmall>
        Two passes over the selected evidence: ten concepts, then the same ten in depth.
      </ParagraphXSmall>

      {error && !prepared ? <Notification kind="negative">{error}</Notification> : null}

      <div className="my-3 grid grid-cols-[repeat(auto-fit,minmax(150px,1fr))] gap-2">
        <Input
          value={query}
          onChange={(event) => {
            setQuery(event.currentTarget.value);
          }}
          placeholder="Search evidence"
        />
        <Select
          options={optionsFor("era_claim")}
          value={era}
          onChange={(value) => {
            setEra(value);
          }}
          placeholder="All eras"
        />
        <Select
          options={optionsFor("tradition")}
          value={tradition}
          onChange={(value) => {
            setTradition(value);
          }}
          placeholder="All traditions"
        />
        <div>
          <LabelSmall className="mb-1 block">Images per run</LabelSmall>
          <Input
            value={imageLimit}
            type="number"
            min={1}
            max={24}
            onChange={(event) => {
              setImageLimit(event.currentTarget.value);
            }}
          />
        </div>
      </div>

      <div className="flex flex-wrap gap-2">
        <Button onClick={prepare} variant="primary">
          Prepare manual run — no API cost
        </Button>
        <Button onClick={start} disabled={busy} variant="secondary">
          {busy ? "Running both passes — this takes a while" : "Run both passes (billed)"}
        </Button>
      </div>

      {prepared ? (
        <div className={card}>
          <LabelSmall>Run these yourself, then paste the result back</LabelSmall>
          <ol className="mt-2 mb-3 pl-5 text-[13px] leading-[1.6] text-ink/70">
            <li>
              Download the zip — every image, both prompts and a manifest. Or save the thumbnails
              one at a time by right-click or long-press.
            </li>
            <li>Copy Pass 1 and send it with those images to ChatGPT or Gemini.</li>
            <li>Send Pass 2 to the same chat to deepen the same ten.</li>
            <li>Copy the JSON it returns and paste it into the box at the bottom.</li>
            <li>Import concepts — ten cards appear here to approve, reject or edit.</li>
          </ol>
          <ParagraphXSmall>
            {String(prepared.evidence_images.length)} images selected. Save them, paste them into
            the model you already pay for with the prompt below, then bring the JSON back.
            Right-click or long-press to save — they deliberately do not open in a new tab, because
            a blocked one loses everything prepared here.
          </ParagraphXSmall>
          <Button size="compact" onClick={downloadBundle} className="mb-2.5">
            Download zip — images + prompts
          </Button>
          <div className="my-2 flex gap-1.5 overflow-x-auto">
            {prepared.evidence_images.map((image) => (
              <img
                key={image.image_url}
                src={image.image_url}
                alt={image.filename}
                title={image.filename}
                className="h-[150px] w-[150px] rounded-[6px] bg-paper-2 object-contain"
              />
            ))}
          </div>
          <div className="mb-1 flex items-center justify-between">
            <LabelSmall>Pass 1</LabelSmall>
            <CopyButton text={prepared.pass1_prompt} label="pass 1 prompt" />
          </div>
          <Textarea value={prepared.pass1_prompt} rows={6} readOnly />
          <div className="mt-2.5">
            <div className="mb-1 flex items-center justify-between">
              <LabelSmall>Pass 2</LabelSmall>
              <CopyButton text={prepared.pass2_prompt} label="pass 2 prompt" />
            </div>
            <Textarea value={prepared.pass2_prompt} rows={3} readOnly />
          </div>
          <div className="mt-3 mb-1 flex items-center justify-between">
            <LabelSmall>Paste the concepts JSON</LabelSmall>
            <PasteButton onPaste={setPasted} label="Paste JSON" />
          </div>
          <Textarea
            value={pasted}
            rows={6}
            placeholder='{"concepts": [...]}'
            onChange={(event) => {
              setPasted(event.currentTarget.value);
            }}
          />
          <Button size="compact" onClick={importPasted} className="mt-2">
            Import concepts
          </Button>
          {error ? <Notification kind="negative" className="mt-2.5">{error}</Notification> : null}
        </div>
      ) : null}

      {runs.length > 0 ? (
        <div className="my-3.5">
          <LabelSmall>Previous runs</LabelSmall>
          <div className="mt-1.5 flex flex-wrap gap-1.5">
            {runs.slice(0, 12).map((previous) => (
              <Button
                key={previous.id}
                size="compact"
                variant={run?.id === previous.id ? "primary" : "secondary"}
                onClick={() => {
                  setRun(previous);
                }}
              >
                {previous.id.slice(0, 8)}
              </Button>
            ))}
          </div>
        </div>
      ) : null}

      {run?.evidence_images && run.evidence_images.length > 0 ? (
        <div className="my-3 flex gap-1.5 overflow-x-auto">
          {run.evidence_images.map((image) => (
            <img
              key={image.image_url}
              src={image.image_url}
              alt={image.filename}
              title={image.filename}
              loading="lazy"
              className="h-[84px] w-[84px] rounded-[6px] bg-paper-2 object-contain"
            />
          ))}
        </div>
      ) : null}

      {(run?.concepts ?? []).map((concept: ResearchConcept) => {
        const prompt =
          drafts[concept.concept_number] ??
          concept.edited_prompt ??
          concept.pass2_prompt ??
          concept.pass1_prompt ??
          "";
        return (
          <article key={concept.concept_number} className={card}>
            <div className="flex flex-wrap items-center gap-2">
              <LabelSmall>
                {String(concept.concept_number)}. {concept.title}
              </LabelSmall>
              <Tag kind={statusKind(concept.status)}>{concept.status ?? "pending"}</Tag>
            </div>
            <ParagraphXSmall>{concept.idea}</ParagraphXSmall>
            <div className="mb-1 flex items-center justify-between">
              <LabelSmall>Generation prompt</LabelSmall>
              <CopyButton text={prompt} label={`prompt ${String(concept.concept_number)}`} />
            </div>
            <Textarea
              value={prompt}
              rows={7}
              onChange={(event) => {
                const next = event.currentTarget.value;
                setDrafts((previous) => ({ ...previous, [concept.concept_number]: next }));
              }}
            />
            <div className="mt-2 flex flex-wrap gap-1.5">
              <Button
                size="compact"
                onClick={() => {
                  applyConcept(concept.concept_number, { status: "approved" });
                }}
              >
                Approve
              </Button>
              <Button
                size="compact"
                variant="secondary"
                onClick={() => {
                  applyConcept(concept.concept_number, { status: "rejected" });
                }}
              >
                Reject
              </Button>
              <Button
                size="compact"
                variant="ghost"
                onClick={() => {
                  applyConcept(concept.concept_number, { prompt });
                }}
              >
                Save edit
              </Button>
            </div>
            {concept.status === "approved" ? (
              <div className="mt-2 flex flex-wrap gap-1.5">
                {/* The primary path, and the one that was missing: a
                    researched concept becomes a numbered concept of its own. */}
                <Button
                  size="compact"
                  onClick={() => {
                    toPipeline(concept.concept_number, true);
                  }}
                >
                  Create a design concept
                </Button>
                {targets.length > 0 ? (
                  <div className="min-w-[220px]">
                    <Select
                      options={targets.map((t) => ({
                        value: t.id,
                        label: `#${String(t.number)} ${t.title}`,
                      }))}
                      value={pipelineTarget}
                      onChange={(value) => {
                        setPipelineTarget(value);
                      }}
                      placeholder="…or add to an existing one"
                    />
                  </div>
                ) : null}
                {targets.length > 0 ? (
                  <Button
                    size="compact"
                    variant="secondary"
                    disabled={pipelineTarget === ""}
                    onClick={() => {
                      toPipeline(concept.concept_number, false);
                    }}
                  >
                    Add to that concept
                  </Button>
                ) : null}
                <Landed result={landed[concept.concept_number]} />
                <ParagraphXSmall className="m-0 basis-full text-ink/50">
                  Opens a design attempt against that concept. No image is generated — make it
                  wherever you make images, then upload it to the attempt.
                </ParagraphXSmall>
                {queued[concept.concept_number] ? (
                  <Tag kind="positive">Attempt {String(queued[concept.concept_number])} created</Tag>
                ) : null}
              </div>
            ) : null}
          </article>
        );
      })}
    </>
  );
}
