"use client";

import { useTransition } from "react";
import { deleteDiscountAction } from "@/app/discounts/actions";
import { Button } from "@/components/ui";

export function DeleteDiscountButton({ id, code }: { id: string; code: string }) {
  const [pending, startTransition] = useTransition();

  return (
    <Button
      type="button"
      variant="danger"
      disabled={pending}
      onClick={() => {
        if (!confirm(`Delete "${code}"? This can't be undone.`)) return;
        startTransition(() => deleteDiscountAction(id));
      }}
    >
      {pending ? "Deleting…" : "Delete"}
    </Button>
  );
}
