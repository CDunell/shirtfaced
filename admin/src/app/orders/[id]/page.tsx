import { notFound } from "next/navigation";
import Link from "next/link";
import { getOrder, orderReference } from "@/db/store-queries";
import { OrderStatusControl } from "@/components/OrderStatusControl";
import { Card } from "@/components/ui";
import { formatCents } from "@/lib/money";

export const dynamic = "force-dynamic";

export default async function OrderDetailPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;
  const order = await getOrder(id);
  if (!order) notFound();

  return (
    <div className="flex flex-col gap-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <h1 className="display text-[40px]">{orderReference(order.orderSeq)}</h1>
        <OrderStatusControl id={order.id} status={order.status} />
      </div>

      <Card className="grid gap-4 sm:grid-cols-2">
        <div>
          <p className="text-[11px] font-bold uppercase tracking-wide text-ink/50">Customer</p>
          {order.customer ? (
            <Link href={`/customers/${order.customer.id}`} className="hover:underline">
              {order.customer.name} — {order.customer.email}
            </Link>
          ) : (
            <p className="text-ink/60">No customer on file</p>
          )}
        </div>
        <div>
          <p className="text-[11px] font-bold uppercase tracking-wide text-ink/50">
            Shipping address
          </p>
          <p className="whitespace-pre-line text-ink/80">
            {order.shippingAddress ?? "—"}
          </p>
        </div>
        {order.discount && (
          <div>
            <p className="text-[11px] font-bold uppercase tracking-wide text-ink/50">
              Discount code
            </p>
            <p className="font-mono">{order.discount.code}</p>
          </div>
        )}
        {order.notes && (
          <div>
            <p className="text-[11px] font-bold uppercase tracking-wide text-ink/50">Notes</p>
            <p className="whitespace-pre-line text-ink/80">{order.notes}</p>
          </div>
        )}
      </Card>

      <div className="flex flex-col gap-3">
        <h2 className="display text-[24px]">Items</h2>
        <div className="flex flex-col gap-2">
          {order.items.map((item) => (
            <Card key={item.id} className="flex flex-wrap items-center gap-4">
              <span className="min-w-[200px] flex-1 font-semibold">{item.productName}</span>
              {item.colourName && (
                <span className="text-[13px] text-ink/50">{item.colourName}</span>
              )}
              {item.size && <span className="text-[13px] text-ink/50">{item.size}</span>}
              <span className="text-[13px] text-ink/50">× {item.quantity}</span>
              <span className="font-semibold">
                {formatCents(item.quantity * item.unitPriceCents)}
              </span>
            </Card>
          ))}
        </div>
      </div>

      <Card className="flex flex-col gap-1 self-end text-[14px] sm:min-w-[280px]">
        <div className="flex justify-between">
          <span className="text-ink/60">Subtotal</span>
          <span>{formatCents(order.subtotalCents)}</span>
        </div>
        <div className="flex justify-between">
          <span className="text-ink/60">Discount</span>
          <span>-{formatCents(order.discountCents)}</span>
        </div>
        <div className="flex justify-between">
          <span className="text-ink/60">Shipping</span>
          <span>{formatCents(order.shippingCents)}</span>
        </div>
        <div className="flex justify-between border-t border-ink/10 pt-1 font-semibold">
          <span>Total</span>
          <span>{formatCents(order.totalCents)}</span>
        </div>
      </Card>
    </div>
  );
}
