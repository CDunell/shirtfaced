"use client";

import { useTransition } from "react";
import { deleteProductAction } from "@/app/products/actions";
import { Button } from "@/components/ui";

export function DeleteProductButton({ id, name }: { id: string; name: string }) {
  const [pending, startTransition] = useTransition();

  return (
    <Button
      type="button"
      variant="danger"
      disabled={pending}
      onClick={() => {
        if (!confirm(`Delete "${name}"? This can't be undone.`)) return;
        startTransition(() => deleteProductAction(id));
      }}
    >
      {pending ? "Deleting…" : "Delete"}
    </Button>
  );
}
