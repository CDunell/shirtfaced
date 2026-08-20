/**
 * Pulls currently-approved designs from Shirtfaced Studio's own database and
 * creates a draft product for each one not already synced — the first thread
 * of "asset lineage" (docs/shirtfaced-audit.md hot-list #8): a design can now
 * be traced from Studio's approval to a storefront listing instead of the two
 * systems sharing nothing but a repo. Run with `npm run sync:approved-designs`.
 *
 * Insert-only, keyed on studio_approved_design_id. A design is created here
 * once and never touched again by this script on later runs, so nothing it
 * writes clobbers a human edit made afterwards in this admin.
 *
 * Every row lands as a draft: published: false, $0.00, one placeholder
 * colourway keyed off production_spec's garment colour, no photography. A
 * human sets the real price, stock and photography and flips it live from
 * /products — this script only proposes. Same reasoning as ADR-010's
 * "a stored image is not an approved image": an approved design is not yet a
 * sellable product either.
 *
 * Same fallback behaviour as scripts/sync-content.mjs and sync-products.mjs:
 * missing or unreachable STUDIO_DATABASE_URL is a quiet no-op, not a failure.
 */
import { config } from "dotenv";
import postgres from "postgres";
import { eq } from "drizzle-orm";
import { db } from "./client";
import { products, productColours } from "./schema";
import { categoryFor, firstSentence, slugFor, garmentColourFor } from "./approved-design-mapping";

config({ path: ".env", override: true });

const SCRIPT = "sync-approved-designs";
const connectionString = process.env.STUDIO_DATABASE_URL;

if (!connectionString) {
  console.log(`${SCRIPT}: STUDIO_DATABASE_URL not set, skipping.`);
  process.exit(0);
}

async function reachable(sql: postgres.Sql): Promise<boolean> {
  try {
    await sql`SELECT 1`;
    return true;
  } catch (error) {
    const why = (error as { code?: string; message: string }).code ?? (error as Error).message;
    console.log(`${SCRIPT}: cannot reach Studio's database (${why}) — skipping.`);
    return false;
  }
}

const studioSql = postgres(connectionString);
if (!(await reachable(studioSql))) {
  await studioSql.end({ timeout: 1 });
  process.exit(0);
}

type ApprovedRow = {
  approved_design_id: string;
  concept_id: string;
  production_spec: Record<string, unknown> | null;
  concept_slug: string;
  title: string;
  concept_text: string | null;
  garments: string[] | null;
};

const rows = (await studioSql`
  SELECT
    ad.id AS approved_design_id,
    ad.concept_id,
    ad.production_spec,
    dc.slug AS concept_slug,
    dc.title,
    dc.concept_text,
    dc.garments
  FROM approved_designs ad
  JOIN design_concepts dc ON dc.id = ad.concept_id
  WHERE ad.superseded_at IS NULL
  ORDER BY ad.approved_at ASC
`) as unknown as ApprovedRow[];

await studioSql.end();

let created = 0;
let skipped = 0;

for (const row of rows) {
  const existing = await db.query.products.findFirst({
    where: eq(products.studioApprovedDesignId, row.approved_design_id),
  });
  if (existing) {
    skipped++;
    continue;
  }

  const garmentColour = garmentColourFor(row.production_spec);

  await db.transaction(async (tx) => {
    const [{ id: productId }] = await tx
      .insert(products)
      .values({
        slug: slugFor(row.concept_slug),
        name: row.title,
        category: categoryFor(row.garments),
        art: row.concept_slug,
        priceCents: 0,
        isNew: true,
        published: false,
        blurb: firstSentence(row.concept_text) || row.title,
        description: (row.concept_text ?? "").trim() || row.title,
        studioConceptId: row.concept_id,
        studioApprovedDesignId: row.approved_design_id,
      })
      .returning({ id: products.id });

    await tx.insert(productColours).values({
      productId,
      name: "Default",
      swatch: garmentColour,
      body: garmentColour,
      ink: "#e8e2d5",
      images: [],
      sortOrder: 0,
    });
  });

  created++;
}

console.log(
  `${SCRIPT}: ${created} draft product(s) created, ${skipped} already synced.` +
    (created > 0 ? " Review, price, photograph and publish them from /products." : ""),
);
process.exit(0);
