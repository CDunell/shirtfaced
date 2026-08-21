import { useEffect, useRef, useState } from "react";

import {
  Button,
  Checkbox,
  cx,
  Input,
  LabelSmall,
  LabelXSmall,
  Notification,
  ParagraphSmall,
  ParagraphXSmall,
  Select,
  Tag,
  Textarea,
} from "./ui";

import { ApiError } from "../api/client";
import {
  assetUrl,
  COLLECTION_ROLES,
  decideAttempt,
  fetchConcepts,
  quickAttemptFromPhrase,
  quickAttemptFromRandomPool,
  submitAttempt,
  uploadAsset,
  type CollectionRole,
  type ConceptView,
  type QuickAttemptResult,
} from "../api/concepts";
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

const ROLE_LABEL: Record<CollectionRole, string> = {
  anchor: "Anchor",
  core: "Core",
  expression: "Expression",
  hero: "Hero",
  collaboration: "Collaboration",
};

type Source = "typed" | "existing" | "dice";
type ItemDecision = "pending" | "kept" | "rejected";

interface BatchItem extends QuickAttemptResult {
  // Local review state -- an uploaded image, and what was done with it.
  assetId: string | null;
  imageUrl: string | null;
  decision: ItemDecision;
  busy: boolean;
  uploadError: string | null;
}

const ELIGIBLE_STATUSES = new Set(["backlog", "ready", "exploring", "held"]);

/**
 * Idea in, upload-ready attempts out -- no brief screen, no queue.
 *
 * Combines this screen's own direct path (type an idea, get a prompt) with
 * the pick-existing / roll-the-dice choices and the prepare-then-return-with-
 * the-file shape from Vintage Research. The one thing neither of those skips
 * is the backend's own gate: an attempt cannot open without a collection role
 * and a graphic archetype (constitution steps 2 and 4, enforced in
 * create_attempt, not a screen's choice). Graphic archetype is filled here
 * from the advisor's own corpus recommendation -- it already computes one.
 * Collection role is a real call nothing in Studio can infer, so it is the
 * one required click below, not a form.
 */
export function DesignPromptBench(): React.JSX.Element {
  const [source, setSource] = useState<Source>("typed");
  const [idea, setIdea] = useState("");
  const [hasGraphic, setHasGraphic] = useState(true);
  const [tradition, setTradition] = useState<string>("novelty");
  const [count, setCount] = useState(1);
  const [role, setRole] = useState<CollectionRole | null>(null);

  const [existing, setExisting] = useState<ConceptView[]>([]);
  const [existingId, setExistingId] = useState("");

  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [batch, setBatch] = useState<BatchItem[]>([]);
  const [lightboxIndex, setLightboxIndex] = useState<number | null>(null);

  useEffect(() => {
    fetchConcepts()
      .then((concepts) => {
        setExisting(concepts.filter((c) => ELIGIBLE_STATUSES.has(c.status)));
      })
      .catch(() => {
        setExisting([]);
      });
  }, []);

  const canGenerate =
    role !== null &&
    !busy &&
    (source === "dice" ||
      (source === "typed" && idea.trim().length > 0) ||
      (source === "existing" && existingId !== ""));

  async function generate(): Promise<void> {
    if (!role) return;
    setBusy(true);
    setError("");
    try {
      const created: QuickAttemptResult[] = [];
      if (source === "dice") {
        for (let i = 0; i < count; i += 1) {
          created.push(await quickAttemptFromRandomPool(tradition, role));
        }
      } else if (source === "existing") {
        const picked = existing.find((c) => c.id === existingId);
        if (!picked) throw new Error("Pick a concept first.");
        created.push(await quickAttemptFromPhrase(picked.concept_text, true, tradition, role));
      } else {
        created.push(await quickAttemptFromPhrase(idea.trim(), hasGraphic, tradition, role));
      }
      setBatch((previous) => [
        ...created.map(
          (result): BatchItem => ({
            ...result,
            assetId: null,
            imageUrl: null,
            decision: "pending",
            busy: false,
            uploadError: null,
          }),
        ),
        ...previous,
      ]);
    } catch (cause) {
      if (cause instanceof ApiError && cause.status === 404) {
        setError(
          `No batch-written concepts for "${tradition}" yet -- this is a first pass covering ` +
            "a handful of traditions, not all of them. Try another tradition, or type your own idea.",
        );
      } else {
        setError(cause instanceof Error ? cause.message : "Something went wrong.");
      }
    } finally {
      setBusy(false);
    }
  }

  function updateItem(attemptId: string, patch: Partial<BatchItem>): void {
    setBatch((previous) =>
      previous.map((item) => (item.attempt_id === attemptId ? { ...item, ...patch } : item)),
    );
  }

  function onFile(item: BatchItem, file: File): void {
    updateItem(item.attempt_id, { busy: true, uploadError: null });
    uploadAsset(item.attempt_id, file)
      .then(async (asset) => {
        // The upload alone leaves the attempt at "generated"; submit moves it
        // to "awaiting_decision", which is what Reject's decision endpoint
        // requires. Done here, not as a separate click -- there is nothing
        // left to decide about submitting once the image exists.
        await submitAttempt(item.attempt_id);
        updateItem(item.attempt_id, {
          assetId: asset.id,
          imageUrl: assetUrl(asset.id),
          busy: false,
        });
      })
      .catch((cause: unknown) => {
        const message = cause instanceof ApiError ? cause.message : "That upload didn't take.";
        updateItem(item.attempt_id, { busy: false, uploadError: message });
      });
  }

  function reject(item: BatchItem): void {
    updateItem(item.attempt_id, { busy: true });
    decideAttempt(item.attempt_id, "rejected", "owner")
      .then(() => {
        updateItem(item.attempt_id, { busy: false, decision: "rejected" });
      })
      .catch((cause: unknown) => {
        const message = cause instanceof ApiError ? cause.message : "That decision didn't save.";
        updateItem(item.attempt_id, { busy: false, uploadError: message });
      });
  }

  function keep(item: BatchItem): void {
    // No further call: the attempt is already awaiting_decision, which is as
    // far as anything can go without the scorecard -- approve-design is
    // gated on it server-side (design_pipeline.guard_decision), and faking
    // that here would just be another button that claims more than it did.
    updateItem(item.attempt_id, { decision: "kept" });
  }

  const withImages = batch.filter((item) => item.imageUrl !== null);
  const activeLightbox = lightboxIndex !== null ? withImages[lightboxIndex] : null;

  return (
    <div className="max-w-[840px]">
      <PageTitle>Prompt</PageTitle>
      <ParagraphSmall className="text-ink/70">
        An idea, an existing concept, or a roll of the dice -- straight to a prompt and an
        upload-ready slot. No brief screen: pick a collection role below, and everything else the
        constitution requires before artwork begins is filled from the corpus.
      </ParagraphSmall>

      {error ? (
        <Notification kind="negative" className="mt-4">
          {error}
        </Notification>
      ) : null}

      <div className="mt-5 flex flex-wrap gap-1.5">
        {(
          [
            ["typed", "Type an idea"],
            ["existing", "Pick existing"],
            ["dice", "Roll the dice"],
          ] as const
        ).map(([id, label]) => (
          <Button
            key={id}
            size="compact"
            variant={source === id ? "primary" : "secondary"}
            onClick={() => {
              setSource(id);
            }}
          >
            {label}
          </Button>
        ))}
      </div>

      {source === "typed" ? (
        <Textarea
          value={idea}
          onChange={(e) => {
            setIdea(e.currentTarget.value);
          }}
          placeholder="e.g. Enormous vintage maritime painting of a tiny speedboat vertical in a monstrous wave, SHE'LL BE RIGHT underneath"
          className="mt-3 min-h-20"
        />
      ) : null}

      {source === "existing" ? (
        <div className="mt-3 min-w-[260px]">
          <Select
            options={existing.map((c) => ({
              value: c.id,
              label: `#${String(c.external_number)} ${c.title}`,
            }))}
            value={existingId}
            onChange={setExistingId}
            placeholder={existing.length ? "Choose a concept" : "Nothing eligible in the backlog"}
          />
        </div>
      ) : null}

      <div className="mt-3 flex flex-wrap items-center gap-4">
        <div className="min-w-[220px]">
          <Select
            options={TRADITIONS.map((t) => ({ value: t, label: t }))}
            value={tradition}
            onChange={setTradition}
          />
        </div>
        {source === "typed" ? (
          <Checkbox checked={hasGraphic} onChange={setHasGraphic}>
            Has a graphic (not text-only)
          </Checkbox>
        ) : null}
        {source === "dice" ? (
          <div className="flex items-center gap-2">
            <LabelSmall>Designs</LabelSmall>
            <Input
              value={String(count)}
              type="number"
              min={1}
              max={10}
              onChange={(e) => {
                const n = Number.parseInt(e.currentTarget.value, 10);
                setCount(Number.isFinite(n) ? Math.min(10, Math.max(1, n)) : 1);
              }}
              className="w-16"
            />
          </div>
        ) : null}
      </div>

      <div className="mt-4">
        <LabelSmall className="mb-1.5 block">
          Collection role -- the one call nothing here can make for you
        </LabelSmall>
        <div className="flex flex-wrap gap-1.5">
          {COLLECTION_ROLES.map((id) => (
            <button
              key={id}
              type="button"
              onClick={() => {
                setRole(id);
              }}
              aria-pressed={role === id}
              className={cx(
                "press appearance-none rounded-full border-none px-3.5 py-2 font-sans text-[13px] font-bold tracking-wide uppercase cursor-pointer",
                role === id ? "bg-ink text-paper" : "bg-paper-2 text-ink/70",
              )}
            >
              {ROLE_LABEL[id]}
            </button>
          ))}
        </div>
      </div>

      <Button
        size="compact"
        isLoading={busy}
        disabled={!canGenerate}
        className="mt-4"
        onClick={() => {
          void generate();
        }}
      >
        {source === "dice"
          ? `Roll ${String(count)} design${count === 1 ? "" : "s"}`
          : "Generate prompt"}
      </Button>
      {!role ? (
        <ParagraphXSmall className="mt-1.5 mb-0 text-ink/50">
          Choose a collection role first -- nothing generates without one.
        </ParagraphXSmall>
      ) : null}

      {batch.length > 0 ? (
        <div className="mt-8 grid gap-4">
          {batch.map((item) => (
            <BatchCard
              key={item.attempt_id}
              item={item}
              onFile={(file) => {
                onFile(item, file);
              }}
              onReject={() => {
                reject(item);
              }}
              onKeep={() => {
                keep(item);
              }}
              onOpenLightbox={() => {
                const index = withImages.findIndex((i) => i.attempt_id === item.attempt_id);
                if (index >= 0) setLightboxIndex(index);
              }}
            />
          ))}
        </div>
      ) : null}

      {activeLightbox ? (
        <Lightbox
          item={activeLightbox}
          hasPrev={lightboxIndex !== null && lightboxIndex > 0}
          hasNext={lightboxIndex !== null && lightboxIndex < withImages.length - 1}
          onClose={() => {
            setLightboxIndex(null);
          }}
          onPrev={() => {
            setLightboxIndex((i) => (i === null ? i : Math.max(0, i - 1)));
          }}
          onNext={() => {
            setLightboxIndex((i) => (i === null ? i : Math.min(withImages.length - 1, i + 1)));
          }}
          onReject={() => {
            reject(activeLightbox);
          }}
          onKeep={() => {
            keep(activeLightbox);
          }}
        />
      ) : null}
    </div>
  );
}

function BatchCard({
  item,
  onFile,
  onReject,
  onKeep,
  onOpenLightbox,
}: {
  item: BatchItem;
  onFile: (file: File) => void;
  onReject: () => void;
  onKeep: () => void;
  onOpenLightbox: () => void;
}): React.JSX.Element {
  const [dragging, setDragging] = useState(false);
  const fileInput = useRef<HTMLInputElement | null>(null);
  const decided = item.decision !== "pending";

  return (
    <div className="rounded-2xl border border-paper-2 p-4">
      <div className="flex flex-wrap items-center gap-2">
        <LabelSmall>
          #{String(item.concept_number)} {item.concept_title}
        </LabelSmall>
        <Tag kind="neutral">{item.collection_role}</Tag>
        <Tag kind="neutral">{item.graphic_archetype.replace(/_/g, " ")}</Tag>
        {item.decision === "kept" ? <Tag kind="positive">Kept</Tag> : null}
        {item.decision === "rejected" ? <Tag kind="negative">Rejected</Tag> : null}
      </div>

      <div className="mt-2 mb-1 flex items-center justify-between">
        <LabelSmall className="mb-0">Prompt</LabelSmall>
        <CopyButton text={item.generation_prompt} label={`prompt ${String(item.concept_number)}`} />
      </div>
      <Textarea value={item.generation_prompt} rows={5} readOnly />

      <div className="mt-3">
        {item.imageUrl ? (
          <button
            type="button"
            onClick={onOpenLightbox}
            className="block w-full cursor-pointer appearance-none border-0 bg-transparent p-0"
          >
            <img
              src={item.imageUrl}
              alt={`${item.concept_title} artwork`}
              className="mx-auto max-h-[220px] rounded-xl bg-[#101010] object-contain"
            />
          </button>
        ) : (
          <div
            onDragOver={(e) => {
              e.preventDefault();
              setDragging(true);
            }}
            onDragLeave={() => {
              setDragging(false);
            }}
            onDrop={(e) => {
              e.preventDefault();
              setDragging(false);
              const file = e.dataTransfer.files[0];
              if (file) onFile(file);
            }}
            onClick={() => fileInput.current?.click()}
            className={cx(
              "cursor-pointer rounded-xl border-2 border-dashed p-[18px] text-center",
              dragging ? "border-lime bg-paper-2" : "border-paper-2 bg-transparent",
            )}
          >
            <ParagraphXSmall className="m-0">
              {item.busy ? "Storing the image…" : "Drop the image here, or click to choose one."}
            </ParagraphXSmall>
            <input
              ref={fileInput}
              type="file"
              accept="image/*"
              aria-label={`Attach the generated image for ${item.concept_title}`}
              className="hidden"
              onChange={(e) => {
                const file = e.currentTarget.files?.[0];
                if (file) onFile(file);
                e.currentTarget.value = "";
              }}
            />
          </div>
        )}
        {item.uploadError ? (
          <ParagraphXSmall className="mt-1.5 mb-0 text-coral">{item.uploadError}</ParagraphXSmall>
        ) : null}
      </div>

      {item.imageUrl && !decided ? (
        <div className="mt-3 flex gap-1.5">
          <Button size="compact" disabled={item.busy} onClick={onKeep}>
            Approve
          </Button>
          <Button size="compact" variant="secondary" disabled={item.busy} onClick={onReject}>
            Reject
          </Button>
        </div>
      ) : null}
      {item.decision === "kept" ? (
        <ParagraphXSmall className="mt-2 mb-0 text-ink/50">
          Kept -- sitting in Work for a full scorecard pass whenever you take it there. Not yet a
          production approval; that still needs the scorecard.
        </ParagraphXSmall>
      ) : null}
    </div>
  );
}

function Lightbox({
  item,
  hasPrev,
  hasNext,
  onClose,
  onPrev,
  onNext,
  onReject,
  onKeep,
}: {
  item: BatchItem;
  hasPrev: boolean;
  hasNext: boolean;
  onClose: () => void;
  onPrev: () => void;
  onNext: () => void;
  onReject: () => void;
  onKeep: () => void;
}): React.JSX.Element {
  useEffect(() => {
    function onKey(e: KeyboardEvent): void {
      if (e.key === "Escape") onClose();
      if (e.key === "ArrowRight" && hasNext) onNext();
      if (e.key === "ArrowLeft" && hasPrev) onPrev();
    }
    window.addEventListener("keydown", onKey);
    return () => {
      window.removeEventListener("keydown", onKey);
    };
  }, [onClose, onNext, onPrev, hasNext, hasPrev]);

  const decided = item.decision !== "pending";

  return (
    <div
      role="dialog"
      aria-modal="true"
      onClick={onClose}
      className="fixed inset-0 z-[100] flex items-center justify-center bg-black/[0.82] p-6"
    >
      <div
        onClick={(e) => {
          e.stopPropagation();
        }}
        className="flex max-h-[92vh] w-full max-w-[900px] flex-col items-center gap-4"
      >
        {item.imageUrl ? (
          <img
            src={item.imageUrl}
            alt={`${item.concept_title} artwork, full size`}
            className="max-h-[68vh] max-w-full rounded-[6px] object-contain"
          />
        ) : null}
        <div className="flex w-full flex-wrap items-center justify-center gap-2">
          <LabelXSmall className="rounded-[3px] bg-paper px-2 py-[3px] text-ink uppercase tracking-[0.04em]">
            #{String(item.concept_number)} {item.concept_title}
          </LabelXSmall>
          {!decided ? (
            <>
              <Button size="compact" disabled={item.busy} onClick={onKeep}>
                Approve
              </Button>
              <Button size="compact" variant="secondary" disabled={item.busy} onClick={onReject}>
                Reject
              </Button>
            </>
          ) : (
            <Tag kind={item.decision === "kept" ? "positive" : "negative"}>{item.decision}</Tag>
          )}
          <Button size="compact" variant="ghost" disabled={!hasPrev} onClick={onPrev}>
            Previous
          </Button>
          <Button size="compact" variant="ghost" disabled={!hasNext} onClick={onNext}>
            Next
          </Button>
          <Button size="compact" variant="ghost" onClick={onClose}>
            Close
          </Button>
        </div>
      </div>
    </div>
  );
}
