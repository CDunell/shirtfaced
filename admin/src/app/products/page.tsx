import Link from "next/link";
import { listProducts } from "@/db/queries";
import { listLowStock, LOW_STOCK_THRESHOLD } from "@/db/store-queries";
import { formatCents } from "@/lib/money";
import { Button, Card } from "@/components/ui";
import { DeleteProductButton } from "@/components/DeleteProductButton";

export const dynamic = "force-dynamic";

export default async function ProductsPage() {
  const [products, lowStock] = await Promise.all([listProducts(), listLowStock()]);

  return (
    <div className="flex flex-col gap-6">
      <div className="flex items-center justify-between">
        <h1 className="display text-[40px]">Products</h1>
        <Link href="/products/new">
          <Button type="button">+ New product</Button>
        </Link>
      </div>

      {lowStock.length > 0 && (
        <div className="rounded-[var(--radius-card)] border border-coral/40 bg-coral/10 p-5">
          <p className="mb-2 text-[13px] font-bold uppercase tracking-wide text-ink">
            Low stock — {lowStock.length} at {String(LOW_STOCK_THRESHOLD)} units or fewer
          </p>
          <div className="flex flex-col gap-1">
            {lowStock.map((row) => (
              <Link
                key={`${row.productId}-${row.colourName}-${row.size}`}
                href={`/products/${row.productId}`}
                className="text-[13px] text-ink/70 hover:text-ink hover:underline"
              >
                {row.productName} — {row.colourName} / {row.size}:{" "}
                <span className="font-semibold">{row.quantity} left</span>
              </Link>
            ))}
          </div>
        </div>
      )}

      {products.length === 0 ? (
        <Card>
          <p className="text-ink/60">No products yet.</p>
        </Card>
      ) : (
        <div className="flex flex-col gap-3">
          {products.map((product) => {
            const totalStock = product.colours.reduce(
              (sum, c) => sum + c.stock.reduce((s, row) => s + row.quantity, 0),
              0,
            );
            return (
              <Card key={product.id} className="flex flex-wrap items-center gap-4">
                <div className="flex min-w-[200px] flex-1 flex-col">
                  <div className="flex items-center gap-2">
                    <span className="font-semibold">{product.name}</span>
                    {product.isNew && (
                      <span className="rounded-full bg-lime px-2 py-0.5 text-[10px] font-bold uppercase">
                        New
                      </span>
                    )}
                    {!product.published && (
                      <span className="rounded-full bg-coral px-2 py-0.5 text-[10px] font-bold uppercase">
                        Draft
                      </span>
                    )}
                    {product.studioApprovedDesignId && (
                      <span className="rounded-full border border-ink/15 px-2 py-0.5 text-[10px] font-bold uppercase text-ink/50">
                        Studio
                      </span>
                    )}
                  </div>
                  <span className="text-[13px] text-ink/50">/{product.slug}</span>
                </div>

                <span className="text-[13px] uppercase tracking-wide text-ink/50">
                  {product.category}
                </span>

                <span className="font-semibold">{formatCents(product.priceCents)}</span>

                <span className="text-[13px] text-ink/50">
                  {product.colours.length} colour{product.colours.length === 1 ? "" : "s"} ·{" "}
                  {totalStock} in stock
                </span>

                <div className="ml-auto flex gap-2">
                  <Link href={`/products/${product.id}`}>
                    <Button type="button" variant="ghost">
                      Edit
                    </Button>
                  </Link>
                  <DeleteProductButton id={product.id} name={product.name} />
                </div>
              </Card>
            );
          })}
        </div>
      )}
    </div>
  );
}
