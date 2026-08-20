"use client";

import { useTransition } from "react";
import { updateOrderStatusAction, deleteOrderAction } from "@/app/orders/actions";
import { ORDER_STATUSES, type OrderStatus } from "@/db/schema";
import { Button } from "@/components/ui";
import { useRouter } from "next/navigation";

export function OrderStatusControl({ id, status }: { id: string; status: OrderStatus }) {
  const [pending, startTransition] = useTransition();
  const router = useRouter();

  return (
    <div className="flex flex-wrap items-center gap-2">
      {ORDER_STATUSES.map((s) => (
        <Button
          key={s}
          type="button"
          variant={s === status ? "primary" : "ghost"}
          disabled={pending || s === status}
          onClick={() => {
            startTransition(() => updateOrderStatusAction(id, s));
          }}
        >
          {s}
        </Button>
      ))}
      <Button
        type="button"
        variant="danger"
        disabled={pending}
        onClick={() => {
          if (!confirm("Delete this order? This can't be undone.")) return;
          startTransition(async () => {
            await deleteOrderAction(id);
            router.push("/orders");
          });
        }}
      >
        Delete
      </Button>
    </div>
  );
}
