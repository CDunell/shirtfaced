import { eq } from "drizzle-orm";
import { db } from "./client";
import { colourStock, productColours, products } from "./schema";
import type { ProductInput } from "@/lib/validation";

export async function listProducts() {
  return db.query.products.findMany({
    with: { colours: { with: { stock: true } } },
    orderBy: (p, { desc }) => desc(p.updatedAt),
  });
}

export async function getProduct(id: string) {
  return db.query.products.findFirst({
    where: eq(products.id, id),
    with: { colours: { with: { stock: true }, orderBy: (c, { asc }) => asc(c.sortOrder) } },
  });
}

async function writeColours(tx: typeof db, productId: string, colours: ProductInput["colours"]) {
  await tx.delete(productColours).where(eq(productColours.productId, productId));

  for (const [index, colour] of colours.entries()) {
    const [{ id: colourId }] = await tx
      .insert(productColours)
      .values({
        productId,
        name: colour.name,
        swatch: colour.swatch,
        body: colour.body,
        ink: colour.ink,
        images: colour.images,
        sortOrder: index,
      })
      .returning({ id: productColours.id });

    const stockRows = Object.entries(colour.stock).map(([size, quantity]) => ({
      colourId,
      size: size as (typeof colourStock.$inferInsert)["size"],
      quantity,
    }));
    if (stockRows.length > 0) {
      await tx.insert(colourStock).values(stockRows);
    }
  }
}

export async function createProduct(data: ProductInput) {
  return db.transaction(async (tx) => {
    const [{ id }] = await tx
      .insert(products)
      .values({
        slug: data.slug,
        name: data.name,
        category: data.category,
        art: data.art,
        priceCents: data.priceCents,
        isNew: data.isNew,
        published: data.published,
        blurb: data.blurb,
        description: data.description,
      })
      .returning({ id: products.id });

    await writeColours(tx as unknown as typeof db, id, data.colours);
    return id;
  });
}

export async function updateProduct(id: string, data: ProductInput) {
  return db.transaction(async (tx) => {
    await tx
      .update(products)
      .set({
        slug: data.slug,
        name: data.name,
        category: data.category,
        art: data.art,
        priceCents: data.priceCents,
        isNew: data.isNew,
        published: data.published,
        blurb: data.blurb,
        description: data.description,
        updatedAt: new Date(),
      })
      .where(eq(products.id, id));

    await writeColours(tx as unknown as typeof db, id, data.colours);
  });
}

export async function deleteProduct(id: string) {
  await db.delete(products).where(eq(products.id, id));
}
