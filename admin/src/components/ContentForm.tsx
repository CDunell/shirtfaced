"use client";

import { useActionState } from "react";
import { Button, Field, Input, Textarea } from "@/components/ui";
import type { FormState } from "@/app/content/actions";

export type ContentFieldDef = {
  name: string;
  label: string;
  type?: "input" | "textarea";
  hint?: string;
  rows?: number;
};

export function ContentForm({
  fields,
  initial,
  action,
}: {
  fields: ContentFieldDef[];
  initial: Record<string, string>;
  action: (prevState: FormState, formData: FormData) => Promise<FormState>;
}) {
  const [state, formAction, pending] = useActionState(action, { error: null });

  return (
    <form action={formAction} className="flex max-w-2xl flex-col gap-5">
      {fields.map((f) => (
        <Field key={f.name} label={f.label} htmlFor={f.name} hint={f.hint}>
          {f.type === "textarea" ? (
            <Textarea
              id={f.name}
              name={f.name}
              defaultValue={initial[f.name]}
              rows={f.rows ?? 3}
              required
            />
          ) : (
            <Input id={f.name} name={f.name} defaultValue={initial[f.name]} required />
          )}
        </Field>
      ))}

      {state.error && (
        <p role="alert" className="text-[13px] font-semibold text-coral">
          {state.error}
        </p>
      )}
      {state.saved && !state.error && (
        <p className="text-[13px] font-semibold text-ink/60">Saved.</p>
      )}

      <Button type="submit" disabled={pending} className="self-start">
        {pending ? "Saving…" : "Save changes"}
      </Button>
    </form>
  );
}
