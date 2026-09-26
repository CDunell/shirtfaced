/**
 * Loads the supplier research in supplier-seed-data.ts into the /suppliers
 * tables. Run with `npm run seed:suppliers`. Insert-only: a supplier, blank
 * or supplier-blank pairing that already exists is left alone, so edits made
 * in the admin are never overwritten and re-running only adds what's new.
 * Suppliers with no print size and no priced record are skipped: a row with
 * nothing to compare is noise.
 */
import { inArray } from "drizzle-orm";
import { db } from "./client";
import { blanks, supplierOfferings, suppliers } from "./schema";
import { SEED_BLANKS, SEED_SUPPLIERS, type BlankKey } from "./supplier-seed-data";

/* When the research was done. */
const CHECKED_AT = new Date("2026-09-26T00:00:00+10:00");

const USEFUL = SEED_SUPPLIERS.filter(
  (s) =>
    s.mw != null ||
    s.sw != null ||
    Object.values(s.o ?? {}).some(
      (o) => o.pc != null || o.spc != null || o.mw != null || o.sw != null || /\d/.test(o.p ?? ""),
    ),
);

async function main() {
  const blankRows = Object.values(SEED_BLANKS);
  const newBlanks = await db.insert(blanks).values(blankRows).onConflictDoNothing().returning({ id: blanks.id });

  const newSuppliers = await db
    .insert(suppliers)
    .values(
      USEFUL.map((s) => ({
        slug: s.s,
        name: s.n,
        kind: s.k,
        location: s.l ?? null,
        region: s.r,
        printsIn: s.pi,
        methods: s.m ?? [],
        minOrder: s.min ?? null,
        minOrderQty: s.mq ?? null,
        maxPrint: s.max ?? null,
        maxPrintWidthMm: s.mw ?? null,
        maxPrintHeightMm: s.mh ?? null,
        standardPrint: s.std ?? null,
        standardPrintWidthMm: s.sw ?? null,
        standardPrintHeightMm: s.sh ?? null,
        website: s.w ?? null,
        integration: s.i ?? null,
        hasAccount: s.acct ?? false,
        sourceUrls: s.src ?? [],
        verification: s.v ?? "summary",
        checkedAt: CHECKED_AT,
        notes: s.nt ?? null,
      })),
    )
    .onConflictDoNothing()
    .returning({ id: suppliers.id });

  const blankIds = new Map(
    (await db.select({ id: blanks.id, slug: blanks.slug }).from(blanks).where(
      inArray(blanks.slug, blankRows.map((b) => b.slug)),
    )).map((b) => [b.slug, b.id]),
  );
  const supplierIds = new Map(
    (await db.select({ id: suppliers.id, slug: suppliers.slug }).from(suppliers).where(
      inArray(suppliers.slug, USEFUL.map((s) => s.s)),
    )).map((s) => [s.slug, s.id]),
  );

  const offerings = USEFUL.flatMap((s) =>
    Object.entries(s.o ?? {}).map(([key, o]) => ({
      supplierId: supplierIds.get(s.s)!,
      blankId: blankIds.get(SEED_BLANKS[key as BlankKey].slug)!,
      status: o.st,
      printedIn: o.pi ?? "unknown",
      maxFront: o.max ?? null,
      maxBack: o.back ?? null,
      maxPrintWidthMm: o.mw ?? null,
      maxPrintHeightMm: o.mh ?? null,
      standardPrint: o.std ?? null,
      standardPrintWidthMm: o.sw ?? null,
      standardPrintHeightMm: o.sh ?? null,
      price: o.p ?? null,
      priceCents: o.pc ?? null,
      standardPriceCents: o.spc ?? null,
      minOrderQty: o.mq ?? null,
      sourceUrl: o.src ?? null,
      verification: o.v ?? s.v ?? "summary",
      checkedAt: CHECKED_AT,
      notes: o.nt ?? null,
    })),
  );
  const newOfferings = offerings.length
    ? await db.insert(supplierOfferings).values(offerings).onConflictDoNothing().returning({ id: supplierOfferings.id })
    : [];

  console.log(
    `Added ${newBlanks.length}/${blankRows.length} blanks, ${newSuppliers.length}/${USEFUL.length} suppliers, ` +
      `${newOfferings.length}/${offerings.length} supplier-blank records (the rest already existed).`,
  );
  process.exit(0);
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
