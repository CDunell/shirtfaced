"use client";

import { useTransition } from "react";
import { deleteFaqItemAction } from "@/app/content/actions";
import { Button } from "@/components/ui";

export function DeleteFaqItemButton({ id, question }: { id: string; question: string }) {
  const [pending, startTransition] = useTransition();

  return (
    <Button
      type="button"
      variant="danger"
      disabled={pending}
      onClick={() => {
        if (!confirm(`Delete "${question}"? This can't be undone.`)) return;
        startTransition(() => deleteFaqItemAction(id));
      }}
    >
      {pending ? "Deleting…" : "Delete"}
    </Button>
  );
}
