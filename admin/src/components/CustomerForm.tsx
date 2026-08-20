"use client";

import { useActionState } from "react";
import { Button, Field, Input, Textarea } from "@/components/ui";
import type { FormState } from "@/app/customers/actions";

export interface CustomerFormValues {
  email: string;
  name: string;
  phone: string;
  addressLine1: string;
  addressLine2: string;
  suburb: string;
  state: string;
  postcode: string;
  country: string;
  notes: string;
}

const BLANK: CustomerFormValues = {
  email: "",
  name: "",
  phone: "",
  addressLine1: "",
  addressLine2: "",
  suburb: "",
  state: "",
  postcode: "",
  country: "AU",
  notes: "",
};

export function CustomerForm({
  initial = BLANK,
  action,
  submitLabel,
}: {
  initial?: CustomerFormValues;
  action: (prevState: FormState, formData: FormData) => Promise<FormState>;
  submitLabel: string;
}) {
  const [state, formAction, pending] = useActionState(action, { error: null });

  return (
    <form action={formAction} className="flex flex-col gap-4">
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
        <Field label="Name" htmlFor="name">
          <Input id="name" name="name" defaultValue={initial.name} required />
        </Field>
        <Field label="Email" htmlFor="email">
          <Input id="email" name="email" type="email" defaultValue={initial.email} required />
        </Field>
      </div>

      <Field label="Phone (optional)" htmlFor="phone">
        <Input id="phone" name="phone" defaultValue={initial.phone} />
      </Field>

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
        <Field label="Address line 1 (optional)" htmlFor="addressLine1">
          <Input id="addressLine1" name="addressLine1" defaultValue={initial.addressLine1} />
        </Field>
        <Field label="Address line 2 (optional)" htmlFor="addressLine2">
          <Input id="addressLine2" name="addressLine2" defaultValue={initial.addressLine2} />
        </Field>
      </div>

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
        <Field label="Suburb (optional)" htmlFor="suburb">
          <Input id="suburb" name="suburb" defaultValue={initial.suburb} />
        </Field>
        <Field label="State (optional)" htmlFor="state">
          <Input id="state" name="state" defaultValue={initial.state} />
        </Field>
        <Field label="Postcode (optional)" htmlFor="postcode">
          <Input id="postcode" name="postcode" defaultValue={initial.postcode} />
        </Field>
      </div>

      <Field label="Country" htmlFor="country">
        <Input id="country" name="country" defaultValue={initial.country} required />
      </Field>

      <Field
        label="Notes (optional)"
        htmlFor="notes"
        hint="Staff-facing only — never shown to the customer."
      >
        <Textarea id="notes" name="notes" defaultValue={initial.notes} rows={3} />
      </Field>

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
