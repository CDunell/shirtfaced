"use client";

import { useTransition } from "react";
import { useRouter } from "next/navigation";
import { deleteCustomerAction } from "@/app/customers/actions";
import { Button } from "@/components/ui";

export function DeleteCustomerButton({ id, name }: { id: string; name: string }) {
  const [pending, startTransition] = useTransition();
  const router = useRouter();

  return (
    <Button
      type="button"
      variant="danger"
      disabled={pending}
      onClick={() => {
        if (!confirm(`Delete "${name}"? This can't be undone.`)) return;
        startTransition(async () => {
          await deleteCustomerAction(id);
          router.push("/customers");
        });
      }}
    >
      {pending ? "Deleting…" : "Delete"}
    </Button>
  );
}
