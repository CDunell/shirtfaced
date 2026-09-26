/**
 * Deletes suppliers we hold no usable figures for: no print size (supplier-
 * wide or per blank) and no price with a number in it. Their blank records go
 * with them (cascade). Run with `npm run prune:suppliers -- --dry` to list
 * what would go, then without `--dry` to delete.
 */
import { inArray } from "drizzle-orm";
import { db } from "./client";
import { suppliers } from "./schema";
import type { SupplierWithOfferings } from "./supplier-queries";

export function hasFigures(s: Pick<SupplierWithOfferings, "maxPrintWidthMm" | "standardPrintWidthMm"> & {
  offerings: Array<Pick<SupplierWithOfferings["offerings"][number], "priceCents" | "standardPriceCents" | "maxPrintWidthMm" | "standardPrintWidthMm" | "price">>;
}): boolean {
  if (s.maxPrintWidthMm || s.standardPrintWidthMm) return true;
  return s.offerings.some(
    (o) =>
      o.priceCents != null ||
      o.standardPriceCents != null ||
      o.maxPrintWidthMm != null ||
      o.standardPrintWidthMm != null ||
      /\d/.test(o.price ?? ""),
  );
}

async function main() {
  const dry = process.argv.includes("--dry");
  const all = await db.query.suppliers.findMany({ with: { offerings: true } });
  const empty = all.filter((s) => !hasFigures(s));
  console.log(`${all.length} suppliers; ${empty.length} with no price or print size; ${all.length - empty.length} kept.`);
  console.log(empty.map((s) => s.name).sort().join(", "));
  if (!dry && empty.length) {
    await db.delete(suppliers).where(inArray(suppliers.id, empty.map((s) => s.id)));
    console.log(`Deleted ${empty.length}.`);
  }
  process.exit(0);
}

if (process.argv[1]?.endsWith("prune-suppliers.ts")) {
  main().catch((err) => {
    console.error(err);
    process.exit(1);
  });
}
