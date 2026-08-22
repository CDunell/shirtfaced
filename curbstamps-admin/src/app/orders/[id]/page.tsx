import { notFound } from "next/navigation";
import Link from "next/link";
import { getOrderById } from "@/db/store-queries";
import { markPaidAction, cancelOrderAction, markShippedAction } from "./actions";

export const dynamic = "force-dynamic";

function money(cents: number) {
  return (cents / 100).toLocaleString("en-AU", { style: "currency", currency: "AUD" });
}

export default async function OrderDetailPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  const order = await getOrderById(id);
  if (!order) notFound();

  return (
    <div>
      <Link href="/orders" className="text-[13px] font-bold text-ink/60">
        ← Orders
      </Link>
      <h1 className="mt-2 text-[26px] font-extrabold">CS-{1000 + order.orderSeq}</h1>
      <p className="mt-1 text-[13px] text-ink/60">
        {order.customer?.name} · {order.customer?.email}
      </p>

      <div className="mt-6 grid gap-6 sm:grid-cols-2">
        <div className="rounded-2xl border border-ink/10 p-4">
          <p className="text-[12px] font-bold tracking-wide text-ink/50 uppercase">Status</p>
          <p className="mt-1 text-[16px] font-bold capitalize">{order.status.replace("_", " ")}</p>
          <p className="mt-3 text-[12px] font-bold tracking-wide text-ink/50 uppercase">Shipping address</p>
          <p className="mt-1 text-[14px]">{order.shippingAddress}</p>
          {order.notes && (
            <>
              <p className="mt-3 text-[12px] font-bold tracking-wide text-ink/50 uppercase">Notes</p>
              <p className="mt-1 text-[13px] text-ink/70">{order.notes}</p>
            </>
          )}
        </div>

        <div className="rounded-2xl border border-ink/10 p-4">
          <p className="text-[12px] font-bold tracking-wide text-ink/50 uppercase">Fulfilment (POD)</p>
          <p className="mt-1 text-[14px]">Provider: {order.podProvider ?? "not submitted"}</p>
          <p className="text-[14px]">POD order: {order.podOrderId ?? "—"}</p>
          <p className="text-[14px]">POD status: {order.podStatus ?? "—"}</p>
          {order.trackingNumber && (
            <p className="text-[14px]">
              Tracking: {order.trackingNumber} {order.carrier ? `(${order.carrier})` : ""}
            </p>
          )}
        </div>
      </div>

      <div className="mt-6 overflow-x-auto rounded-2xl border border-ink/10">
        <table className="w-full min-w-[520px] text-left text-[14px]">
          <thead className="bg-paper-2">
            <tr>
              <th className="px-4 py-3 font-bold">Item</th>
              <th className="px-4 py-3 font-bold">Colour</th>
              <th className="px-4 py-3 font-bold">Size</th>
              <th className="px-4 py-3 font-bold">Qty</th>
              <th className="px-4 py-3 font-bold">Price</th>
            </tr>
          </thead>
          <tbody>
            {order.items.map((item) => (
              <tr key={item.id} className="border-t border-ink/8">
                <td className="px-4 py-3">{item.productName}</td>
                <td className="px-4 py-3">{item.colourName ?? "—"}</td>
                <td className="px-4 py-3">{item.size ?? "—"}</td>
                <td className="px-4 py-3">{item.quantity}</td>
                <td className="px-4 py-3">{money(item.unitPriceCents)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <div className="mt-4 flex justify-end gap-1 text-[14px]">
        <p className="mr-auto font-bold">
          Subtotal {money(order.subtotalCents)} + shipping {money(order.shippingCents)} ={" "}
          <span className="text-[18px]">{money(order.totalCents)}</span>
        </p>
      </div>

      <div className="mt-6 flex flex-wrap gap-2">
        {order.status === "pending" && (
          <form action={markPaidAction.bind(null, order.id)}>
            <button className="h-10 rounded-full bg-ink px-4 text-[13px] font-bold text-paper">
              Mark paid &amp; submit to POD
            </button>
          </form>
        )}
        {(order.status === "paid" || order.status === "in_production") && (
          <form action={markShippedAction.bind(null, order.id)}>
            <button className="h-10 rounded-full bg-green-600 px-4 text-[13px] font-bold text-white">
              Mark shipped
            </button>
          </form>
        )}
        {order.status !== "cancelled" && order.status !== "shipped" && (
          <form action={cancelOrderAction.bind(null, order.id)}>
            <button className="h-10 rounded-full border border-red-300 px-4 text-[13px] font-bold text-red-600">
              Cancel &amp; refund
            </button>
          </form>
        )}
      </div>
    </div>
  );
}
