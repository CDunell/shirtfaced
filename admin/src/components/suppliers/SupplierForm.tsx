"use client";

import { useActionState } from "react";
import { Button, Checkbox, Field, Input, Select, Textarea } from "@/components/ui";
import type { FormState } from "@/app/suppliers/actions";
import type { Supplier } from "@/db/supplier-queries";
import { PRINT_REGIONS, SUPPLIER_KINDS, VERIFICATIONS } from "@/db/schema";
import { KIND_LABEL, REGION_LABEL, VERIFICATION_LABEL } from "./labels";

const REGIONS = ["QLD", "NSW", "ACT", "VIC", "TAS", "WA", "SA", "NT", "AU", "NZ", "INTL"];

const cm = (mm: number | null) => (mm == null ? "" : String(mm / 10));

export function SupplierForm({
  supplier,
  action,
}: {
  supplier: Supplier;
  action: (prev: FormState, formData: FormData) => Promise<FormState>;
}) {
  const [state, formAction, pending] = useActionState(action, { error: null });

  return (
    <form action={formAction} className="flex flex-col gap-4">
      <div className="grid gap-4 sm:grid-cols-2">
        <Field label="Name" htmlFor="s-name">
          <Input id="s-name" name="name" defaultValue={supplier.name} required />
        </Field>
        <Field label="Type" htmlFor="s-kind">
          <Select id="s-kind" name="kind" defaultValue={supplier.kind}>
            {SUPPLIER_KINDS.map((k) => <option key={k} value={k}>{KIND_LABEL[k]}</option>)}
          </Select>
        </Field>
        <Field label="Location" htmlFor="s-location">
          <Input id="s-location" name="location" defaultValue={supplier.location ?? ""} />
        </Field>
        <Field label="Region" htmlFor="s-region">
          <Select id="s-region" name="region" defaultValue={supplier.region}>
            {REGIONS.map((r) => <option key={r} value={r}>{r}</option>)}
          </Select>
        </Field>
        <Field label="Prints Australian orders in" htmlFor="s-printsIn">
          <Select id="s-printsIn" name="printsIn" defaultValue={supplier.printsIn}>
            {PRINT_REGIONS.map((r) => <option key={r} value={r}>{REGION_LABEL[r]}</option>)}
          </Select>
        </Field>
        <Field label="Methods" htmlFor="s-methods" hint="Comma-separated, e.g. DTG, DTF, screen">
          <Input id="s-methods" name="methods" defaultValue={supplier.methods.join(", ")} />
        </Field>
        <Field label="Minimum order, as they word it" htmlFor="s-minOrder">
          <Input id="s-minOrder" name="minOrder" defaultValue={supplier.minOrder ?? ""} />
        </Field>
        <Field label="Minimum order (number)" htmlFor="s-minOrderQty" hint="Used for sorting and 'best'">
          <Input id="s-minOrderQty" name="minOrderQty" inputMode="numeric" defaultValue={supplier.minOrderQty ?? ""} />
        </Field>
        <Field label="Largest print, as they word it" htmlFor="s-maxPrint">
          <Input id="s-maxPrint" name="maxPrint" defaultValue={supplier.maxPrint ?? ""} />
        </Field>
        <div className="grid grid-cols-2 gap-3">
          <Field label="Width (cm)" htmlFor="s-maxW">
            <Input id="s-maxW" name="maxPrintWidthMm" inputMode="decimal" defaultValue={cm(supplier.maxPrintWidthMm)} />
          </Field>
          <Field label="Height (cm)" htmlFor="s-maxH">
            <Input id="s-maxH" name="maxPrintHeightMm" inputMode="decimal" defaultValue={cm(supplier.maxPrintHeightMm)} />
          </Field>
        </div>
        <Field label="Standard print (what the base price includes)" htmlFor="s-standardPrint" hint="e.g. A4, 21 × 29.7 cm">
          <Input id="s-standardPrint" name="standardPrint" defaultValue={supplier.standardPrint ?? ""} />
        </Field>
        <div className="grid grid-cols-2 gap-3">
          <Field label="Std width (cm)" htmlFor="s-stdW">
            <Input id="s-stdW" name="standardPrintWidthMm" inputMode="decimal" defaultValue={cm(supplier.standardPrintWidthMm)} />
          </Field>
          <Field label="Std height (cm)" htmlFor="s-stdH">
            <Input id="s-stdH" name="standardPrintHeightMm" inputMode="decimal" defaultValue={cm(supplier.standardPrintHeightMm)} />
          </Field>
        </div>
        <Field label="Website" htmlFor="s-website">
          <Input id="s-website" name="website" type="url" defaultValue={supplier.website ?? ""} />
        </Field>
        <Field label="How orders reach them" htmlFor="s-integration" hint="API, Shopify app, Printify provider, email quote…">
          <Input id="s-integration" name="integration" defaultValue={supplier.integration ?? ""} />
        </Field>
        <Field label="Trust" htmlFor="s-verification">
          <Select id="s-verification" name="verification" defaultValue={supplier.verification}>
            {VERIFICATIONS.map((v) => <option key={v} value={v}>{VERIFICATION_LABEL[v]}</option>)}
          </Select>
        </Field>
        <label className="flex items-center gap-2 self-end pb-3 text-[14px]">
          <Checkbox id="s-hasAccount" name="hasAccount" defaultChecked={supplier.hasAccount} />
          We have an account with them
        </label>
      </div>
      <Field label="Notes" htmlFor="s-notes">
        <Textarea id="s-notes" name="notes" rows={4} defaultValue={supplier.notes ?? ""} />
      </Field>
      {state.error && <p className="text-[13px] text-coral">{state.error}</p>}
      {state.saved && !state.error && <p className="text-[13px] text-ink/60">Saved.</p>}
      <div>
        <Button type="submit" disabled={pending}>{pending ? "Saving…" : "Save supplier"}</Button>
      </div>
    </form>
  );
}
