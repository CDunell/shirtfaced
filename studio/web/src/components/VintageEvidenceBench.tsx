/**
 * Browsing the cached marketplace evidence.
 *
 * Two collectors write into one root -- sold eBay listings, and the design
 * archive gathered from vintage resellers and collector communities -- so a
 * record's marketplace decides how its source link is labelled, and an absent
 * brand is shown as a dash rather than "Unknown". Brand is left empty on
 * purpose where the source never stated one: the filters match exactly, and a
 * brand guessed from a reseller's title would quietly poison them.
 *
 * Filtering happens here rather than server-side. The whole set is a few
 * thousand rows of small JSON, and holding it in memory makes the era and
 * tradition counts honest -- each option can say how much it will actually
 * return before it is chosen.
 */

import { useEffect, useMemo, useState } from "react";

import { Button, Input, Notification, Select, Tag, LabelSmall, ParagraphXSmall, type SelectOption } from "./ui";
import { PageTitle } from "./chrome";

import { ApiError, fetchEvidence, type EvidenceManifest, type EvidenceRecord } from "../api/client";

/** Thumbnails per card. Enough to judge a graphic, few enough to scroll. */
const THUMBS = 4;

/** Rows rendered at once. The archive runs to thousands; the screen does not. */
const PAGE = 60;

function options(records: EvidenceRecord[], key: keyof EvidenceRecord): SelectOption[] {
  const counts = new Map<string, number>();
  for (const record of records) {
    const value = String(record[key] ?? "").trim();
    if (value) counts.set(value, (counts.get(value) ?? 0) + 1);
  }
  return [...counts.entries()]
    .sort((a, b) => b[1] - a[1] || a[0].localeCompare(b[0]))
    .map(([id, n]) => ({ value: id, label: `${id} (${String(n)})` }));
}

export function VintageEvidenceBench(): React.JSX.Element {
  const [records, setRecords] = useState<EvidenceRecord[]>([]);
  const [manifest, setManifest] = useState<EvidenceManifest>({});
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [query, setQuery] = useState("");
  const [brand, setBrand] = useState<string>("");
  const [era, setEra] = useState<string>("");
  const [tradition, setTradition] = useState<string>("");
  const [shown, setShown] = useState(PAGE);

  useEffect(() => {
    const controller = new AbortController();
    fetchEvidence(controller.signal)
      .then((data) => {
        setRecords(data.records);
        setManifest(data.manifest);
        setLoading(false);
      })
      .catch((cause: unknown) => {
        if (controller.signal.aborted) return;
        setError(cause instanceof ApiError ? cause.message : "Evidence cache unavailable.");
        setLoading(false);
      });
    return () => {
      controller.abort();
    };
  }, []);

  const brands = useMemo(() => options(records, "brand"), [records]);
  const eras = useMemo(() => options(records, "era_claim"), [records]);
  const traditions = useMemo(() => options(records, "tradition"), [records]);

  const matched = useMemo(() => {
    const q = query.trim().toLowerCase();
    const b = brand;
    const e = era;
    const t = tradition;
    return records.filter((r) => {
      if (b && r.brand !== b) return false;
      if (e && r.era_claim !== e) return false;
      if (t && r.tradition !== t) return false;
      if (!q) return true;
      // Coalesced: an absent field would otherwise interpolate the literal
      // "undefined" into the haystack, and a search for it would match every
      // record the collectors left incomplete.
      const hay = [r.brand, r.title, r.era_claim, r.tradition]
        .map((value) => value ?? "")
        .join(" ");
      return hay.toLowerCase().includes(q);
    });
  }, [records, query, brand, era, tradition]);

  return (
    <>
      <PageTitle
        meta={
          loading
            ? "Loading"
            : `${String(records.length)} cached listings · ${String(manifest.image_count ?? 0)} images`
        }
      >
        Vintage Evidence
      </PageTitle>
      <ParagraphXSmall>
        Sold surf, skate and street references with retained listing photography.
      </ParagraphXSmall>

      {error ? <Notification kind="negative">{error}</Notification> : null}

      <div className="my-3 grid grid-cols-[repeat(auto-fit,minmax(180px,1fr))] gap-2">
        <Input
          value={query}
          onChange={(event) => {
            setQuery(event.currentTarget.value);
            setShown(PAGE);
          }}
          placeholder="Search titles"
        />
        <Select
          options={brands}
          value={brand}
          onChange={(value) => {
            setBrand(value);
            setShown(PAGE);
          }}
          placeholder="All brands"
        />
        <Select
          options={eras}
          value={era}
          onChange={(value) => {
            setEra(value);
            setShown(PAGE);
          }}
          placeholder="All eras"
        />
        <Select
          options={traditions}
          value={tradition}
          onChange={(value) => {
            setTradition(value);
            setShown(PAGE);
          }}
          placeholder="All traditions"
        />
      </div>

      <LabelSmall>
        {matched.length} matching {matched.length === 1 ? "listing" : "listings"}
      </LabelSmall>

      <div className="mt-2.5 grid grid-cols-[repeat(auto-fill,minmax(240px,1fr))] gap-2.5">
        {matched.slice(0, shown).map((record) => (
          <article
            key={record.listing_id}
            className="flex flex-col gap-1.5 rounded-[10px] border border-ink/10 p-2.5"
          >
            <div className="flex gap-1 overflow-x-auto">
              {record.images.slice(0, THUMBS).map((src) => (
                <img
                  key={src}
                  src={src}
                  alt=""
                  loading="lazy"
                  className="h-[70px] w-[70px] rounded-[6px] bg-paper-2 object-contain"
                />
              ))}
            </div>
            <LabelSmall>{record.brand || "—"}</LabelSmall>
            <ParagraphXSmall className="m-0 break-words">
              {record.title || "Untitled"}
            </ParagraphXSmall>
            <div className="flex flex-wrap gap-1">
              {record.era_claim ? <Tag kind="accent">{record.era_claim}</Tag> : null}
              {record.tradition ? <Tag kind="neutral">{record.tradition}</Tag> : null}
              <Tag kind="neutral">{record.images.length} images</Tag>
            </div>
            {record.source_url ? (
              <a href={record.source_url} rel="noreferrer" className="text-xs text-ink">
                {record.marketplace === "archive" ? "Source" : "eBay"} ↗
              </a>
            ) : null}
          </article>
        ))}
      </div>

      {shown < matched.length ? (
        <Button
          variant="secondary"
          size="compact"
          onClick={() => {
            setShown((n) => n + PAGE);
          }}
          className="mt-3.5"
        >
          Show more ({matched.length - shown} remaining)
        </Button>
      ) : null}
    </>
  );
}
