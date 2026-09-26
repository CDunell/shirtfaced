"use client";

import { useActionState } from "react";
import { Button, Field, Input, Select, Textarea } from "@/components/ui";
import { createBlankAction, type FormState } from "@/app/suppliers/actions";
import { BLANK_CATEGORIES } from "@/db/schema";
import { CATEGORY_LABEL } from "./labels";

export function BlankForm() {
  const [state, formAction, pending] = useActionState<FormState, FormData>(createBlankAction, { error: null });
  return (
    <form action={formAction} className="flex flex-col gap-4">
      <div className="grid gap-4 sm:grid-cols-3">
        <Field label="Brand" htmlFor="b-brand">
          <Input id="b-brand" name="brand" placeholder="AS Colour" required />
        </Field>
        <Field label="Style code" htmlFor="b-style">
          <Input id="b-style" name="styleCode" placeholder="5080" required />
        </Field>
        <Field label="Name" htmlFor="b-name">
          <Input id="b-name" name="name" placeholder="Heavy Tee" required />
        </Field>
        <Field label="Type" htmlFor="b-category">
          <Select id="b-category" name="category" defaultValue="tee">
            {BLANK_CATEGORIES.map((c) => <option key={c} value={c}>{CATEGORY_LABEL[c]}</option>)}
          </Select>
        </Field>
        <Field label="GSM" htmlFor="b-gsm">
          <Input id="b-gsm" name="gsm" inputMode="numeric" placeholder="280" />
        </Field>
        <Field label="Fit" htmlFor="b-fit">
          <Input id="b-fit" name="fit" placeholder="Relaxed, boxy" />
        </Field>
      </div>
      <Field label="Notes" htmlFor="b-notes">
        <Textarea id="b-notes" name="notes" rows={2} />
      </Field>
      {state.error && <p className="text-[13px] text-coral">{state.error}</p>}
      <div>
        <Button type="submit" disabled={pending}>{pending ? "Adding…" : "Add blank"}</Button>
      </div>
    </form>
  );
}
