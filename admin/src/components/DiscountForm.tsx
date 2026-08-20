"use client";

import { useActionState, useState } from "react";
import { Button, Checkbox, Field, Input, Select } from "@/components/ui";
import type { FormState } from "@/app/discounts/actions";
import type { DiscountType } from "@/db/schema";

export interface DiscountFormValues {
  code: string;
  type: DiscountType;
  value: string;
  active: boolean;
  startsAt: string;
  expiresAt: string;
  usageLimit: string;
}

const BLANK: DiscountFormValues = {
  code: "",
  type: "percent",
  value: "",
  active: true,
  startsAt: "",
  expiresAt: "",
  usageLimit: "",
};

/** yyyy-mm-dd, what an <input type="date"> wants. */
function toDateInputValue(iso: string): string {
  return iso ? iso.slice(0, 10) : "";
}

export function DiscountForm({
  initial = BLANK,
  action,
  submitLabel,
}: {
  initial?: DiscountFormValues;
  action: (prevState: FormState, formData: FormData) => Promise<FormState>;
  submitLabel: string;
}) {
  const [state, formAction, pending] = useActionState(action, { error: null });
  const [type, setType] = useState<DiscountType>(initial.type);

  return (
    <form action={formAction} className="flex flex-col gap-4">
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
        <Field label="Code" htmlFor="code" hint="Letters, numbers, - and _ only.">
          <Input id="code" name="code" defaultValue={initial.code} required />
        </Field>
        <Field label="Type" htmlFor="type">
          <Select
            id="type"
            name="type"
            defaultValue={initial.type}
            onChange={(e) => {
              setType(e.target.value as DiscountType);
            }}
          >
            <option value="percent">Percent off</option>
            <option value="fixed">Fixed amount off</option>
          </Select>
        </Field>
        <Field
          label={type === "percent" ? "Value (%)" : "Value (cents)"}
          htmlFor="value"
          hint={type === "fixed" ? "e.g. 1000 = $10.00 off" : undefined}
        >
          <Input
            id="value"
            name="value"
            type="number"
            min={0}
            max={type === "percent" ? 100 : undefined}
            defaultValue={initial.value}
            required
          />
        </Field>
      </div>

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
        <Field label="Starts (optional)" htmlFor="startsAt">
          <Input
            id="startsAt"
            name="startsAt"
            type="date"
            defaultValue={toDateInputValue(initial.startsAt)}
          />
        </Field>
        <Field label="Expires (optional)" htmlFor="expiresAt">
          <Input
            id="expiresAt"
            name="expiresAt"
            type="date"
            defaultValue={toDateInputValue(initial.expiresAt)}
          />
        </Field>
        <Field label="Usage limit (optional)" htmlFor="usageLimit" hint="Blank = unlimited.">
          <Input
            id="usageLimit"
            name="usageLimit"
            type="number"
            min={1}
            defaultValue={initial.usageLimit}
          />
        </Field>
      </div>

      <label className="flex items-center gap-2 text-[13px] font-semibold text-ink">
        <Checkbox name="active" defaultChecked={initial.active} />
        Active
      </label>

      {state.error && (
        <p role="alert" className="text-[13px] font-semibold text-coral">
          {state.error}
        </p>
      )}

      <Button type="submit" disabled={pending} className="self-start">
        {pending ? "Saving…" : submitLabel}
      </Button>
    </form>
  );
}
