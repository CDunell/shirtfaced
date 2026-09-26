"use client";

import { useActionState } from "react";
import { Button, Field, Input, Select, Textarea } from "@/components/ui";
import type { FormState } from "@/app/suppliers/actions";
import type { Blank, Offering } from "@/db/supplier-queries";
import { OFFER_STATUSES, PRINT_REGIONS, VERIFICATIONS } from "@/db/schema";
import { REGION_LABEL, STATUS_LABEL, VERIFICATION_LABEL } from "./labels";

const cm = (mm: number | null | undefined) => (mm == null ? "" : String(mm / 10));
const dollars = (cents: number | null | undefined) => (cents == null ? "" : (cents / 100).toFixed(2));

/* One form for both editing an offering (blank fixed) and adding one (blank picked). */
export function OfferingForm({
  offering,
  blank,
  addableBlanks,
  action,
}: {
  offering?: Offering;
  blank?: Blank;
  addableBlanks?: Blank[];
  action: (prev: FormState, formData: FormData) => Promise<FormState>;
}) {
  const [state, formAction, pending] = useActionState(action, { error: null });
  const key = offering?.id ?? "new";

  return (
    <form action={formAction} className="flex flex-col gap-3">
      {blank ? (
        <input type="hidden" name="blankId" value={blank.id} />
      ) : (
        <Field label="Blank" htmlFor={`o-${key}-blank`}>
          <Select id={`o-${key}-blank`} name="blankId" defaultValue="">
            <option value="" disabled>Pick a blank</option>
            {(addableBlanks ?? []).map((b) => (
              <option key={b.id} value={b.id}>{b.brand} {b.styleCode} · {b.name}</option>
            ))}
          </Select>
        </Field>
      )}
      <div className="grid gap-3 sm:grid-cols-3">
        <Field label="Offers it" htmlFor={`o-${key}-status`}>
          <Select id={`o-${key}-status`} name="status" defaultValue={offering?.status ?? "yes"}>
            {OFFER_STATUSES.map((s) => <option key={s} value={s}>{STATUS_LABEL[s]}</option>)}
          </Select>
        </Field>
        <Field label="Printed in" htmlFor={`o-${key}-printedIn`}>
          <Select id={`o-${key}-printedIn`} name="printedIn" defaultValue={offering?.printedIn ?? "unknown"}>
            {PRINT_REGIONS.map((r) => <option key={r} value={r}>{REGION_LABEL[r]}</option>)}
          </Select>
        </Field>
        <Field label="Trust" htmlFor={`o-${key}-verification`}>
          <Select id={`o-${key}-verification`} name="verification" defaultValue={offering?.verification ?? "page"}>
            {VERIFICATIONS.map((v) => <option key={v} value={v}>{VERIFICATION_LABEL[v]}</option>)}
          </Select>
        </Field>
        <Field label="Max front, as stated" htmlFor={`o-${key}-front`}>
          <Input id={`o-${key}-front`} name="maxFront" defaultValue={offering?.maxFront ?? ""} />
        </Field>
        <Field label="Max back, as stated" htmlFor={`o-${key}-back`}>
          <Input id={`o-${key}-back`} name="maxBack" defaultValue={offering?.maxBack ?? ""} />
        </Field>
        <div className="grid grid-cols-2 gap-2">
          <Field label="W (cm)" htmlFor={`o-${key}-w`}>
            <Input id={`o-${key}-w`} name="maxPrintWidthMm" inputMode="decimal" defaultValue={cm(offering?.maxPrintWidthMm)} />
          </Field>
          <Field label="H (cm)" htmlFor={`o-${key}-h`}>
            <Input id={`o-${key}-h`} name="maxPrintHeightMm" inputMode="decimal" defaultValue={cm(offering?.maxPrintHeightMm)} />
          </Field>
        </div>
        <Field label="Standard print, as stated" htmlFor={`o-${key}-std`} hint="What the base price includes, e.g. A4">
          <Input id={`o-${key}-std`} name="standardPrint" defaultValue={offering?.standardPrint ?? ""} />
        </Field>
        <div className="grid grid-cols-2 gap-2">
          <Field label="Std W (cm)" htmlFor={`o-${key}-sw`}>
            <Input id={`o-${key}-sw`} name="standardPrintWidthMm" inputMode="decimal" defaultValue={cm(offering?.standardPrintWidthMm)} />
          </Field>
          <Field label="Std H (cm)" htmlFor={`o-${key}-sh`}>
            <Input id={`o-${key}-sh`} name="standardPrintHeightMm" inputMode="decimal" defaultValue={cm(offering?.standardPrintHeightMm)} />
          </Field>
        </div>
        <Field label="Price, as stated" htmlFor={`o-${key}-price`}>
          <Input id={`o-${key}-price`} name="price" defaultValue={offering?.price ?? ""} />
        </Field>
        <Field label="A$ 1 tee + standard print" htmlFor={`o-${key}-spc`} hint="Only if their figures add up exactly">
          <Input id={`o-${key}-spc`} name="standardPriceCents" inputMode="decimal" defaultValue={dollars(offering?.standardPriceCents)} />
        </Field>
        <Field label="A$ 1 tee + largest print" htmlFor={`o-${key}-pc`} hint="Only if their figures add up exactly">
          <Input id={`o-${key}-pc`} name="priceCents" inputMode="decimal" defaultValue={dollars(offering?.priceCents)} />
        </Field>
        <Field label="Minimum (number)" htmlFor={`o-${key}-min`}>
          <Input id={`o-${key}-min`} name="minOrderQty" inputMode="numeric" defaultValue={offering?.minOrderQty ?? ""} />
        </Field>
      </div>
      <Field label="Source URL" htmlFor={`o-${key}-src`}>
        <Input id={`o-${key}-src`} name="sourceUrl" type="url" defaultValue={offering?.sourceUrl ?? ""} />
      </Field>
      <Field label="Notes" htmlFor={`o-${key}-notes`}>
        <Textarea id={`o-${key}-notes`} name="notes" rows={2} defaultValue={offering?.notes ?? ""} />
      </Field>
      {state.error && <p className="text-[13px] text-coral">{state.error}</p>}
      {state.saved && !state.error && <p className="text-[13px] text-ink/60">Saved.</p>}
      <div>
        <Button type="submit" disabled={pending}>{pending ? "Saving…" : offering ? "Save" : "Add"}</Button>
      </div>
    </form>
  );
}
