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
import { useStyletron } from "baseui";
import { Button, KIND as BUTTON_KIND, SIZE } from "baseui/button";
import { Input } from "baseui/input";
import { Notification, KIND as NOTIFICATION_KIND } from "baseui/notification";
import { Select, type Value } from "baseui/select";
import { Tag, KIND as TAG_KIND } from "baseui/tag";
import { Textarea } from "baseui/textarea";
import { LabelSmall, ParagraphXSmall } from "baseui/typography";

import { CopyButton, PasteButton, PageTitle } from "./chrome";

import {
  ApiError,
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
  type ResearchConcept,
  type ResearchRun,
} from "../api/client";

function statusKind(status: string | undefined): (typeof TAG_KIND)[keyof typeof TAG_KIND] {
  if (status === "approved") return TAG_KIND.positive;
  if (status === "rejected") return TAG_KIND.negative;
  return TAG_KIND.neutral;
}

export function VintageResearchBench(): React.JSX.Element {
  const [css, theme] = useStyletron();
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
  const [era, setEra] = useState<Value>([]);
  const [tradition, setTradition] = useState<Value>([]);
  const [records, setRecords] = useState<EvidenceRecord[]>([]);
  const [imageLimit, setImageLimit] = useState("16");
  const [drafts, setDrafts] = useState<Record<number, string>>({});
  const [pipelineTarget, setPipelineTarget] = useState<Value>([]);
  // Attempt number per concept, so the button reports what it created
  // rather than leaving a click with nothing to show for it.
  const [queued, setQueued] = useState<Record<number, number>>({});
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
    (key: "era_claim" | "tradition"): Value => {
      const counts = new Map<string, number>();
      for (const record of records) {
        const value = (record[key] ?? "").trim();
        if (value) counts.set(value, (counts.get(value) ?? 0) + 1);
      }
      return [...counts.entries()]
        .sort((a, b) => b[1] - a[1] || a[0].localeCompare(b[0]))
        .map(([id, n]) => ({ id, label: `${id} (${String(n)})` }));
    },
    [records],
  );

  const start = useCallback(() => {
    setBusy(true);
    setError(null);
    const limit = Number.parseInt(imageLimit, 10);
    startResearchRun({
      query,
      era: String(era[0]?.id ?? ""),
      tradition: String(tradition[0]?.id ?? ""),
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
      era: String(era[0]?.id ?? ""),
      tradition: String(tradition[0]?.id ?? ""),
      image_limit: Number.isFinite(limit) ? limit : 16,
    })
      .then((result) => {
        setPrepared(result);
      })
      .catch((cause: unknown) => {
        setError(cause instanceof ApiError ? cause.message : "Could not select evidence.");
      });
  }, [query, era, tradition, imageLimit]);

  const importPasted = useCallback(() => {
    setError(null);
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

  const toPipeline = useCallback(
    (number: number) => {
      const target = pipelineTarget[0]?.id;
      if (!run || target === undefined) return;
      sendConceptToPipeline(run.id, number, String(target))
        .then((result) => {
          setError(null);
          setQueued((previous) => ({ ...previous, [number]: result.attempt_number }));
        })
        .catch((cause: unknown) => {
          setError(cause instanceof ApiError ? cause.message : "Could not queue that concept.");
        });
    },
    [run, pipelineTarget],
  );

  const card = css({
    border: `1px solid ${theme.colors.borderOpaque}`,
    borderRadius: "10px",
    padding: "12px",
    marginBottom: "12px",
  });

  return (
    <>
      <PageTitle meta={run ? `Run ${run.id.slice(0, 8)}` : `${String(runs.length)} runs`}>
        Vintage Research
      </PageTitle>
      <ParagraphXSmall>
        Two passes over the selected evidence: ten concepts, then the same ten in depth.
      </ParagraphXSmall>

      {error ? (
        <Notification
          kind={NOTIFICATION_KIND.negative}
          overrides={{ Body: { style: { width: "auto" } } }}
        >
          {error}
        </Notification>
      ) : null}

      <div
        className={css({
          display: "grid",
          gridTemplateColumns: "repeat(auto-fit, minmax(150px, 1fr))",
          gap: "8px",
          margin: "12px 0",
        })}
      >
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
          onChange={(params) => {
            setEra(params.value);
          }}
          placeholder="All eras"
        />
        <Select
          options={optionsFor("tradition")}
          value={tradition}
          onChange={(params) => {
            setTradition(params.value);
          }}
          placeholder="All traditions"
        />
        <div>
          <LabelSmall overrides={{ Block: { style: { marginBottom: "4px", marginTop: 0 } } }}>
            Images per run
          </LabelSmall>
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

      <div className={css({ display: "flex", gap: "8px", flexWrap: "wrap" })}>
        <Button onClick={prepare} kind={BUTTON_KIND.primary}>
          Prepare manual run — no API cost
        </Button>
        <Button onClick={start} disabled={busy} isLoading={busy} kind={BUTTON_KIND.secondary}>
          {busy ? "Running both passes — this takes a while" : "Run both passes (billed)"}
        </Button>
      </div>

      {prepared ? (
        <div className={card}>
          <LabelSmall>Run these yourself, then paste the result back</LabelSmall>
          <ParagraphXSmall>
            {String(prepared.evidence_images.length)} images selected. Save them, paste them into
            the model you already pay for with the prompt below, then bring the JSON back.
            Right-click or long-press to save — they deliberately do not open in a new tab, because
            a blocked one loses everything prepared here.
          </ParagraphXSmall>
          <div className={css({ display: "flex", gap: "6px", overflowX: "auto", margin: "8px 0" })}>
            {prepared.evidence_images.map((image) => (
              <img
                key={image.image_url}
                src={image.image_url}
                alt={image.filename}
                title={image.filename}
                className={css({
                  width: "150px",
                  height: "150px",
                  objectFit: "contain",
                  background: theme.colors.backgroundSecondary,
                  borderRadius: "6px",
                })}
              />
            ))}
          </div>
          <div
            className={css({
              display: "flex",
              alignItems: "center",
              justifyContent: "space-between",
              marginBottom: "4px",
            })}
          >
            <LabelSmall>Pass 1</LabelSmall>
            <CopyButton text={prepared.pass1_prompt} label="pass 1 prompt" />
          </div>
          <Textarea value={prepared.pass1_prompt} rows={6} readOnly />
          <div className={css({ marginTop: "10px" })}>
            <div
              className={css({
                display: "flex",
                alignItems: "center",
                justifyContent: "space-between",
                marginBottom: "4px",
              })}
            >
              <LabelSmall>Pass 2</LabelSmall>
              <CopyButton text={prepared.pass2_prompt} label="pass 2 prompt" />
            </div>
            <Textarea value={prepared.pass2_prompt} rows={3} readOnly />
          </div>
          <div
            className={css({
              display: "flex",
              alignItems: "center",
              justifyContent: "space-between",
              marginTop: "12px",
              marginBottom: "4px",
            })}
          >
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
          <Button
            size={SIZE.compact}
            onClick={importPasted}
            disabled={pasted.trim().length === 0}
            overrides={{ BaseButton: { style: { marginTop: "8px" } } }}
          >
            Import concepts
          </Button>
        </div>
      ) : null}

      {runs.length > 0 ? (
        <div className={css({ margin: "14px 0" })}>
          <LabelSmall>Previous runs</LabelSmall>
          <div className={css({ display: "flex", gap: "6px", flexWrap: "wrap", marginTop: "6px" })}>
            {runs.slice(0, 12).map((previous) => (
              <Button
                key={previous.id}
                size={SIZE.mini}
                kind={run?.id === previous.id ? BUTTON_KIND.primary : BUTTON_KIND.secondary}
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
        <div className={css({ display: "flex", gap: "6px", overflowX: "auto", margin: "12px 0" })}>
          {run.evidence_images.map((image) => (
            <img
              key={image.image_url}
              src={image.image_url}
              alt={image.filename}
              title={image.filename}
              loading="lazy"
              className={css({
                width: "84px",
                height: "84px",
                objectFit: "contain",
                background: theme.colors.backgroundSecondary,
                borderRadius: "6px",
              })}
            />
          ))}
        </div>
      ) : null}

      {run?.concepts.map((concept: ResearchConcept) => {
        const prompt =
          drafts[concept.concept_number] ??
          concept.edited_prompt ??
          concept.pass2_prompt ??
          concept.pass1_prompt ??
          "";
        return (
          <article key={concept.concept_number} className={card}>
            <div
              className={css({
                display: "flex",
                gap: "8px",
                alignItems: "center",
                flexWrap: "wrap",
              })}
            >
              <LabelSmall>
                {String(concept.concept_number)}. {concept.title}
              </LabelSmall>
              <Tag closeable={false} kind={statusKind(concept.status)}>
                {concept.status ?? "pending"}
              </Tag>
            </div>
            <ParagraphXSmall>{concept.idea}</ParagraphXSmall>
            <div
              className={css({
                display: "flex",
                alignItems: "center",
                justifyContent: "space-between",
                marginBottom: "4px",
              })}
            >
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
            <div
              className={css({ display: "flex", gap: "6px", flexWrap: "wrap", marginTop: "8px" })}
            >
              <Button
                size={SIZE.compact}
                onClick={() => {
                  applyConcept(concept.concept_number, { status: "approved" });
                }}
              >
                Approve
              </Button>
              <Button
                size={SIZE.compact}
                kind={BUTTON_KIND.secondary}
                onClick={() => {
                  applyConcept(concept.concept_number, { status: "rejected" });
                }}
              >
                Reject
              </Button>
              <Button
                size={SIZE.compact}
                kind={BUTTON_KIND.tertiary}
                onClick={() => {
                  applyConcept(concept.concept_number, { prompt });
                }}
              >
                Save edit
              </Button>
            </div>
            {concept.status === "approved" && targets.length > 0 ? (
              <div
                className={css({ display: "flex", gap: "6px", marginTop: "8px", flexWrap: "wrap" })}
              >
                <div className={css({ minWidth: "220px" })}>
                  <Select
                    size={SIZE.compact}
                    options={targets.map((t) => ({
                      id: t.id,
                      label: `#${String(t.number)} ${t.title}`,
                    }))}
                    value={pipelineTarget}
                    onChange={(params) => {
                      setPipelineTarget(params.value);
                    }}
                    placeholder="Design concept"
                  />
                </div>
                <Button
                  size={SIZE.compact}
                  disabled={pipelineTarget.length === 0}
                  onClick={() => {
                    toPipeline(concept.concept_number);
                  }}
                >
                  Send to design pipeline
                </Button>
                {queued[concept.concept_number] !== undefined ? (
                  <Tag closeable={false} kind={TAG_KIND.positive}>
                    Attempt {String(queued[concept.concept_number])} created
                  </Tag>
                ) : null}
              </div>
            ) : null}
          </article>
        );
      })}
    </>
  );
}
