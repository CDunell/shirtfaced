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

import { PageTitle } from "./chrome";

import {
  ApiError,
  fetchDesignConceptTargets,
  fetchResearchRun,
  fetchResearchRuns,
  sendConceptToPipeline,
  startResearchRun,
  updateResearchConcept,
  type DesignConceptTarget,
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
  const [era, setEra] = useState("");
  const [tradition, setTradition] = useState("");
  const [imageLimit, setImageLimit] = useState("16");
  const [drafts, setDrafts] = useState<Record<number, string>>({});
  const [pipelineTarget, setPipelineTarget] = useState<Value>([]);
  // Attempt number per concept, so the button reports what it created
  // rather than leaving a click with nothing to show for it.
  const [queued, setQueued] = useState<Record<number, number>>({});

  useEffect(() => {
    const controller = new AbortController();
    void Promise.all([
      fetchResearchRuns(controller.signal),
      fetchDesignConceptTargets(controller.signal),
    ])
      .then(([loadedRuns, loadedTargets]) => {
        setRuns(loadedRuns);
        setTargets(loadedTargets);
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
        <Input
          value={era}
          onChange={(event) => {
            setEra(event.currentTarget.value);
          }}
          placeholder="Era, e.g. 1990s"
        />
        <Input
          value={tradition}
          onChange={(event) => {
            setTradition(event.currentTarget.value);
          }}
          placeholder="Tradition"
        />
        <Input
          value={imageLimit}
          onChange={(event) => {
            setImageLimit(event.currentTarget.value);
          }}
          placeholder="Images"
        />
      </div>

      <Button onClick={start} disabled={busy} isLoading={busy}>
        {busy ? "Running both passes — this takes a while" : "Run both passes"}
      </Button>

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
