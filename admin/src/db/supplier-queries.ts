import { asc, eq, inArray, sql } from "drizzle-orm";
import { db } from "./client";
import {
  blanks,
  supplierOfferings,
  suppliers,
  type BlankCategory,
  type OfferStatus,
  type PrintRegion,
  type SupplierKind,
  type Verification,
} from "./schema";

export type Blank = typeof blanks.$inferSelect;
export type Supplier = typeof suppliers.$inferSelect;
export type Offering = typeof supplierOfferings.$inferSelect;
export type SupplierWithOfferings = Supplier & { offerings: Offering[] };

export async function listBlanks(): Promise<Blank[]> {
  return db.select().from(blanks).orderBy(asc(blanks.sortOrder), asc(blanks.brand), asc(blanks.styleCode));
}

export async function listSuppliersWithOfferings(): Promise<SupplierWithOfferings[]> {
  return db.query.suppliers.findMany({
    with: { offerings: true },
    orderBy: (s, { asc: a }) => [a(s.name)],
  });
}

export async function getSupplierBySlug(slug: string): Promise<SupplierWithOfferings | undefined> {
  return db.query.suppliers.findFirst({
    where: eq(suppliers.slug, slug),
    with: { offerings: true },
  });
}

export async function getSuppliersBySlugs(slugs: string[]): Promise<SupplierWithOfferings[]> {
  if (slugs.length === 0) return [];
  return db.query.suppliers.findMany({
    where: inArray(suppliers.slug, slugs),
    with: { offerings: true },
  });
}

export type SupplierInput = {
  name: string;
  kind: SupplierKind;
  location: string | null;
  region: string;
  printsIn: PrintRegion;
  methods: string[];
  minOrder: string | null;
  minOrderQty: number | null;
  maxPrint: string | null;
  maxPrintWidthMm: number | null;
  maxPrintHeightMm: number | null;
  standardPrint: string | null;
  standardPrintWidthMm: number | null;
  standardPrintHeightMm: number | null;
  website: string | null;
  integration: string | null;
  hasAccount: boolean;
  verification: Verification;
  notes: string | null;
};

export async function updateSupplier(id: string, input: SupplierInput): Promise<void> {
  await db
    .update(suppliers)
    .set({ ...input, checkedAt: new Date(), updatedAt: new Date() })
    .where(eq(suppliers.id, id));
}

export type OfferingInput = {
  status: OfferStatus;
  printedIn: PrintRegion;
  maxFront: string | null;
  maxBack: string | null;
  maxPrintWidthMm: number | null;
  maxPrintHeightMm: number | null;
  standardPrint: string | null;
  standardPrintWidthMm: number | null;
  standardPrintHeightMm: number | null;
  price: string | null;
  priceCents: number | null;
  standardPriceCents: number | null;
  minOrderQty: number | null;
  sourceUrl: string | null;
  verification: Verification;
  notes: string | null;
};

export async function upsertOffering(
  supplierId: string,
  blankId: string,
  input: OfferingInput,
): Promise<void> {
  const values = { ...input, checkedAt: new Date(), updatedAt: new Date() };
  await db
    .insert(supplierOfferings)
    .values({ supplierId, blankId, ...values })
    .onConflictDoUpdate({
      target: [supplierOfferings.supplierId, supplierOfferings.blankId],
      set: values,
    });
}

export type BlankInput = {
  slug: string;
  brand: string;
  styleCode: string;
  name: string;
  category: BlankCategory;
  gsm: number | null;
  fit: string | null;
  fibre: string | null;
  yarn: string | null;
  construction: string | null;
  dye: string | null;
  printNotes: string | null;
  specUrl: string | null;
  notes: string | null;
};

export async function createBlank(input: BlankInput): Promise<void> {
  const [{ max }] = await db
    .select({ max: sql<number>`coalesce(max(${blanks.sortOrder}), 0)` })
    .from(blanks);
  await db.insert(blanks).values({ ...input, sortOrder: Number(max) + 10 });
}
