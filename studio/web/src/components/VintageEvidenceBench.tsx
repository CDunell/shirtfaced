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
import { useStyletron } from "baseui";
import { Button, KIND as BUTTON_KIND, SIZE } from "baseui/button";
import { Input } from "baseui/input";
import { Notification, KIND as NOTIFICATION_KIND } from "baseui/notification";
import { Select, type Value } from "baseui/select";
import { Tag, KIND as TAG_KIND } from "baseui/tag";
import { LabelSmall, ParagraphXSmall } from "baseui/typography";

import { PageTitle } from "./chrome";

import { ApiError, fetchEvidence, type EvidenceManifest, type EvidenceRecord } from "../api/client";

/** Thumbnails per card. Enough to judge a graphic, few enough to scroll. */
const THUMBS = 4;

/** Rows rendered at once. The archive runs to thousands; the screen does not. */
const PAGE = 60;

function options(records: EvidenceRecord[], key: keyof EvidenceRecord): Value {
  const counts = new Map<string, number>();
  for (const record of records) {
    const value = String(record[key] ?? "").trim();
    if (value) counts.set(value, (counts.get(value) ?? 0) + 1);
  }
  return [...counts.entries()]
    .sort((a, b) => b[1] - a[1] || a[0].localeCompare(b[0]))
    .map(([id, n]) => ({ id, label: `${id} (${String(n)})` }));
}

export function VintageEvidenceBench(): React.JSX.Element {
  const [css, theme] = useStyletron();
  const [records, setRecords] = useState<EvidenceRecord[]>([]);
  const [manifest, setManifest] = useState<EvidenceManifest>({});
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [query, setQuery] = useState("");
  const [brand, setBrand] = useState<Value>([]);
  const [era, setEra] = useState<Value>([]);
  const [tradition, setTradition] = useState<Value>([]);
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
    const b = brand[0]?.id;
    const e = era[0]?.id;
    const t = tradition[0]?.id;
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

  const card = css({
    border: `1px solid ${theme.colors.borderOpaque}`,
    borderRadius: "10px",
    padding: "10px",
    display: "flex",
    flexDirection: "column",
    gap: "6px",
  });

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
          gridTemplateColumns: "repeat(auto-fit, minmax(180px, 1fr))",
          gap: "8px",
          margin: "12px 0",
        })}
      >
        <Input
          value={query}
          onChange={(event) => {
            setQuery(event.currentTarget.value);
            setShown(PAGE);
          }}
          placeholder="Search titles"
          clearable
        />
        <Select
          options={brands}
          value={brand}
          onChange={(params) => {
            setBrand(params.value);
            setShown(PAGE);
          }}
          placeholder="All brands"
        />
        <Select
          options={eras}
          value={era}
          onChange={(params) => {
            setEra(params.value);
            setShown(PAGE);
          }}
          placeholder="All eras"
        />
        <Select
          options={traditions}
          value={tradition}
          onChange={(params) => {
            setTradition(params.value);
            setShown(PAGE);
          }}
          placeholder="All traditions"
        />
      </div>

      <LabelSmall>
        {matched.length} matching {matched.length === 1 ? "listing" : "listings"}
      </LabelSmall>

      <div
        className={css({
          display: "grid",
          gridTemplateColumns: "repeat(auto-fill, minmax(240px, 1fr))",
          gap: "10px",
          marginTop: "10px",
        })}
      >
        {matched.slice(0, shown).map((record) => (
          <article key={record.listing_id} className={card}>
            <div className={css({ display: "flex", gap: "4px", overflowX: "auto" })}>
              {record.images.slice(0, THUMBS).map((src) => (
                <img
                  key={src}
                  src={src}
                  alt=""
                  loading="lazy"
                  className={css({
                    width: "70px",
                    height: "70px",
                    objectFit: "contain",
                    background: theme.colors.backgroundSecondary,
                    borderRadius: "6px",
                  })}
                />
              ))}
            </div>
            <LabelSmall>{record.brand || "—"}</LabelSmall>
            <ParagraphXSmall
              overrides={{ Block: { style: { margin: 0, wordBreak: "break-word" } } }}
            >
              {record.title || "Untitled"}
            </ParagraphXSmall>
            <div className={css({ display: "flex", gap: "4px", flexWrap: "wrap" })}>
              {record.era_claim ? (
                <Tag closeable={false} kind={TAG_KIND.accent}>
                  {record.era_claim}
                </Tag>
              ) : null}
              {record.tradition ? (
                <Tag closeable={false} kind={TAG_KIND.neutral}>
                  {record.tradition}
                </Tag>
              ) : null}
              <Tag closeable={false} kind={TAG_KIND.neutral}>
                {record.images.length} images
              </Tag>
            </div>
            {record.source_url ? (
              <a
                href={record.source_url}
                rel="noreferrer"
                className={css({ fontSize: "12px", color: theme.colors.contentPrimary })}
              >
                {record.marketplace === "archive" ? "Source" : "eBay"} ↗
              </a>
            ) : null}
          </article>
        ))}
      </div>

      {shown < matched.length ? (
        <Button
          kind={BUTTON_KIND.secondary}
          size={SIZE.compact}
          onClick={() => {
            setShown((n) => n + PAGE);
          }}
          overrides={{ BaseButton: { style: { marginTop: "14px" } } }}
        >
          Show more ({matched.length - shown} remaining)
        </Button>
      ) : null}
    </>
  );
}
