import Link from "next/link";
import { listOrders } from "@/db/store-queries";

export const dynamic = "force-dynamic";

function money(cents: number) {
  return (cents / 100).toLocaleString("en-AU", { style: "currency", currency: "AUD" });
}

const STATUS_COLOUR: Record<string, string> = {
  pending: "bg-yellow-200 text-yellow-900",
  paid: "bg-blue-200 text-blue-900",
  in_production: "bg-purple-200 text-purple-900",
  shipped: "bg-green-200 text-green-900",
  cancelled: "bg-red-200 text-red-900",
};

export default async function OrdersPage() {
  const orders = await listOrders();

  return (
    <div>
      <h1 className="text-[26px] font-extrabold">Orders</h1>
      <p className="mt-1 text-[13px] text-ink/60">{orders.length} total.</p>

      {/* Table on wider screens — a 640px-min table would otherwise sit inside
          an overflow-x-auto box with no visible scroll affordance on mobile,
          reading as a cut-off table rather than a scrollable one. */}
      <div className="mt-6 hidden overflow-x-auto rounded-2xl border border-ink/10 sm:block">
        <table className="w-full min-w-[640px] text-left text-[14px]">
          <thead className="bg-paper-2">
            <tr>
              <th className="px-4 py-3 font-bold">Order</th>
              <th className="px-4 py-3 font-bold">Customer</th>
              <th className="px-4 py-3 font-bold">Status</th>
              <th className="px-4 py-3 font-bold">POD</th>
              <th className="px-4 py-3 font-bold">Total</th>
              <th className="px-4 py-3 font-bold">Placed</th>
            </tr>
          </thead>
          <tbody>
            {orders.map((order) => (
              <tr key={order.id} className="border-t border-ink/8 hover:bg-paper-2/60">
                <td className="px-4 py-3">
                  <Link href={`/orders/${order.id}`} className="font-bold underline underline-offset-2">
                    CS-{1000 + order.orderSeq}
                  </Link>
                </td>
                <td className="px-4 py-3">{order.customer?.name ?? "—"}</td>
                <td className="px-4 py-3">
                  <span className={`rounded-full px-2 py-1 text-[12px] font-bold ${STATUS_COLOUR[order.status]}`}>
                    {order.status.replace("_", " ")}
                  </span>
                </td>
                <td className="px-4 py-3 text-[13px] text-ink/60">{order.podStatus ?? "—"}</td>
                <td className="px-4 py-3 font-semibold">{money(order.totalCents)}</td>
                <td className="px-4 py-3 text-[13px] text-ink/60">
                  {new Date(order.createdAt).toLocaleDateString("en-AU")}
                </td>
              </tr>
            ))}
            {orders.length === 0 && (
              <tr>
                <td colSpan={6} className="px-4 py-8 text-center text-ink/50">
                  No orders yet.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      {/* Stacked cards on narrow screens — no horizontal scroll at all. */}
      <div className="mt-6 flex flex-col gap-3 sm:hidden">
        {orders.map((order) => (
          <Link
            key={order.id}
            href={`/orders/${order.id}`}
            className="block rounded-2xl border border-ink/10 p-4 active:bg-paper-2/60"
          >
            <div className="flex items-center justify-between gap-2">
              <span className="font-bold underline underline-offset-2">CS-{1000 + order.orderSeq}</span>
              <span className={`rounded-full px-2 py-1 text-[12px] font-bold ${STATUS_COLOUR[order.status]}`}>
                {order.status.replace("_", " ")}
              </span>
            </div>
            <div className="mt-2 text-[14px]">{order.customer?.name ?? "—"}</div>
            <div className="mt-1 flex items-center justify-between text-[13px] text-ink/60">
              <span>{order.podStatus ?? "—"}</span>
              <span className="font-semibold text-ink">{money(order.totalCents)}</span>
            </div>
            <div className="mt-1 text-[12px] text-ink/50">
              {new Date(order.createdAt).toLocaleDateString("en-AU")}
            </div>
          </Link>
        ))}
        {orders.length === 0 && (
          <div className="rounded-2xl border border-ink/10 p-8 text-center text-ink/50">No orders yet.</div>
        )}
      </div>
    </div>
  );
}
