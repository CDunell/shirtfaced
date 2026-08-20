import Link from "next/link";
import { listOrders, orderReference } from "@/db/store-queries";
import { formatCents } from "@/lib/money";
import { Button, Card } from "@/components/ui";

export const dynamic = "force-dynamic";

const STATUS_STYLE: Record<string, string> = {
  pending: "bg-paper-2 text-ink/70",
  paid: "bg-lime text-ink",
  fulfilled: "bg-ink text-paper",
  cancelled: "bg-coral text-ink",
};

export default async function OrdersPage() {
  const orders = await listOrders();

  return (
    <div className="flex flex-col gap-6">
      <div className="flex items-center justify-between">
        <h1 className="display text-[40px]">Orders</h1>
        <Link href="/orders/new">
          <Button type="button">+ Record order</Button>
        </Link>
      </div>

      {orders.length === 0 ? (
        <Card>
          <p className="text-ink/60">
            No orders yet — the storefront has no checkout wired up, so nothing lands here on its
            own. Use &ldquo;Record order&rdquo; for a phone or email sale.
          </p>
        </Card>
      ) : (
        <div className="flex flex-col gap-3">
          {orders.map((order) => (
            <Link key={order.id} href={`/orders/${order.id}`}>
              <Card className="flex flex-wrap items-center gap-4 hover:bg-white/80">
                <span className="font-mono text-[13px]">{orderReference(order.orderSeq)}</span>
                <span
                  className={`rounded-full px-2 py-0.5 text-[10px] font-bold uppercase ${
                    STATUS_STYLE[order.status] ?? ""
                  }`}
                >
                  {order.status}
                </span>
                <span className="min-w-[160px] flex-1 text-[13px] text-ink/70">
                  {order.customer?.name ?? "No customer on file"}
                </span>
                <span className="font-semibold">{formatCents(order.totalCents)}</span>
              </Card>
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}
