"use client";

import { useState, useTransition } from "react";
import { setOrderTrackingAction } from "@/app/orders/actions";
import { Button, Field, Input } from "@/components/ui";

export function TrackingControl({
  id,
  trackingNumber,
  carrier,
}: {
  id: string;
  trackingNumber: string | null;
  carrier: string | null;
}) {
  const [tracking, setTracking] = useState(trackingNumber ?? "");
  const [carrierName, setCarrierName] = useState(carrier ?? "");
  const [pending, startTransition] = useTransition();

  return (
    <div className="grid gap-3 sm:grid-cols-[1fr_1fr_auto] sm:items-end">
      <Field label="Tracking number" htmlFor="tracking-number">
        <Input
          id="tracking-number"
          value={tracking}
          onChange={(e) => setTracking(e.target.value)}
          placeholder="e.g. 1234567890"
        />
      </Field>
      <Field label="Carrier" htmlFor="tracking-carrier">
        <Input
          id="tracking-carrier"
          value={carrierName}
          onChange={(e) => setCarrierName(e.target.value)}
          placeholder="e.g. Australia Post"
        />
      </Field>
      <Button
        type="button"
        disabled={pending || !tracking.trim()}
        onClick={() => {
          startTransition(async () => {
            const result = await setOrderTrackingAction(id, tracking, carrierName);
            if (result.error) alert(result.error);
          });
        }}
      >
        {trackingNumber ? "Update" : "Save & notify"}
      </Button>
    </div>
  );
}
