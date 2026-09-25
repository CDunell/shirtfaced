/**
 * Pulls kept renders from Shirtfaced Studio's Gallery review queue and
 * creates a draft product for each one not already synced.
 *
 * The generation-queue counterpart to sync-approved-designs.ts: that script
 * follows the concept-library pipeline (brief, attempt, scorecard, approved
 * version); this one follows the newer path -- an evidence-informed engine
 * renders a design, a person opens Gallery and marks it kept or dropped, and
 * a kept one belongs in the store. No scorecard, no brief, no production
 * spec -- Approve in Gallery is the only gate. Run with
 * `npm run sync:kept-generations`.
 *
 * Insert-only, keyed on studio_generation_sample_id. A design is created
 * here once and never touched again by this script on later runs, so
 * nothing it writes clobbers a human edit made afterwards in this admin.
 *
 * Every row lands as a draft: published: false, $0.00, one placeholder
 * colourway -- but, unlike sync-approved-designs.ts, images is NOT empty.
 * A kept sample already has a real rendered image (that's what "kept"
 * means), so the draft starts pre-filled with it, hot-linked from Studio's
 * own asset store via STUDIO_URL. A human still sets the real price, stock
 * and final photography and flips it live from /products -- this script
 * only proposes -- but they now have something to look at while deciding,
 * not an empty gallery.
 *
 * Same fallback behaviour as scripts/sync-content.mjs and sync-products.mjs:
 * missing or unreachable STUDIO_DATABASE_URL is a quiet no-op, not a failure.
 */
import { config } from "dotenv";
import postgres from "postgres";
import { eq } from "drizzle-orm";
import { db } from "./client";
import { products, productColours } from "./schema";
import { slugForGeneration, nameForGeneration, firstSentence } from "./approved-design-mapping";

config({ path: ".env", override: true });

const SCRIPT = "sync-kept-generations";
const connectionString = process.env.STUDIO_DATABASE_URL;
const studioUrl = process.env.STUDIO_URL ?? "https://studio.shirtfaced.wtf";

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

type KeptRow = {
  id: string;
  tradition: string;
  concept_text: string;
};

const rows = (await studioSql`
  SELECT id, tradition, concept_text
  FROM design_generation_samples
  WHERE status = 'kept'
  ORDER BY created_at ASC
`) as unknown as KeptRow[];

await studioSql.end();

let created = 0;
let skipped = 0;

for (const row of rows) {
  const existing = await db.query.products.findFirst({
    where: eq(products.studioGenerationSampleId, row.id),
  });
  if (existing) {
    skipped++;
    continue;
  }

  const imageUrl = `${studioUrl}/api/design/generations/${row.id}/image?variant=full`;

  await db.transaction(async (tx) => {
    const [{ id: productId }] = await tx
      .insert(products)
      .values({
        slug: slugForGeneration(row.tradition, row.id),
        name: nameForGeneration(row.tradition, row.id),
        category: "tees",
        art: row.tradition,
        priceCents: 0,
        isNew: true,
        published: false,
        blurb: firstSentence(row.concept_text) || row.tradition,
        description: (row.concept_text ?? "").trim() || row.tradition,
        studioGenerationSampleId: row.id,
      })
      .returning({ id: products.id });

    await tx.insert(productColours).values({
      productId,
      name: "Default",
      swatch: "#1c1c1a",
      body: "#1c1c1a",
      ink: "#e8e2d5",
      images: [imageUrl],
      sortOrder: 0,
    });
  });

  created++;
}

console.log(
  `${SCRIPT}: ${created} draft product(s) created, ${skipped} already synced.` +
    (created > 0 ? " Review, price, finalise photography and publish them from /products." : ""),
);
process.exit(0);
