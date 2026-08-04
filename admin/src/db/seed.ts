/**
 * One-time import of the storefront's static catalog into Postgres. Run with
 * `npm run seed`. Safe to re-run — it replaces everything each time, so
 * don't run it after the DB becomes the source of truth and admins have made
 * edits.
 *
 * seed-data.json is a point-in-time snapshot of ../../../src/lib/products.ts
 * (dumped once, not imported live) so this app stays deployable on its own —
 * it doesn't depend on the storefront's source tree being present.
 *
 * The static catalog has no inventory concept, so every size on every
 * colourway is seeded with DEFAULT_STOCK units. Adjust real quantities in
 * the admin UI afterwards.
 */
import { db } from "./client";
import {
  products as productsTable,
  productColours,
  colourStock,
  type Category,
  type Size,
} from "./schema";
import seedData from "./seed-data.json";

type SeedProduct = {
  slug: string;
  name: string;
  price: number;
  category: string;
  art: string;
  isNew?: boolean;
  blurb: string;
  description: string;
  sizes: string[];
  colours: {
    name: string;
    swatch: string;
    body: string;
    ink: string;
    images?: string[];
  }[];
};

const staticProducts = seedData as SeedProduct[];

const DEFAULT_STOCK = 20;

async function main() {
  await db.transaction(async (tx) => {
    await tx.delete(productsTable);

    for (const product of staticProducts) {
      const [{ id: productId }] = await tx
        .insert(productsTable)
        .values({
          slug: product.slug,
          name: product.name,
          category: product.category as Category,
          art: product.art,
          priceCents: Math.round(product.price * 100),
          isNew: product.isNew ?? false,
          blurb: product.blurb,
          description: product.description,
        })
        .returning({ id: productsTable.id });

      for (const [index, colour] of product.colours.entries()) {
        const [{ id: colourId }] = await tx
          .insert(productColours)
          .values({
            productId,
            name: colour.name,
            swatch: colour.swatch,
            body: colour.body,
            ink: colour.ink,
            images: colour.images ?? [],
            sortOrder: index,
          })
          .returning({ id: productColours.id });

        await tx.insert(colourStock).values(
          product.sizes.map((size) => ({
            colourId,
            size: size as Size,
            quantity: DEFAULT_STOCK,
          })),
        );
      }
    }
  });

  console.log(`Seeded ${staticProducts.length} products.`);
  process.exit(0);
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
