"use client";

import { useActionState, useId, useState } from "react";
import { useRouter } from "next/navigation";
import { SIZES } from "@/db/schema";
import type { FormState } from "@/app/orders/actions";
import { Button, Card, Field, Input, Label, Select, Textarea } from "@/components/ui";
import { formatCents } from "@/lib/money";

type ItemState = {
  productName: string;
  colourName: string;
  size: string;
  quantity: string;
  unitPriceDollars: string;
};

function newItem(): ItemState {
  return { productName: "", colourName: "", size: "", quantity: "1", unitPriceDollars: "0.00" };
}

export interface OrderFormCustomer {
  id: string;
  name: string;
  email: string;
}

export interface OrderFormDiscount {
  id: string;
  code: string;
}

export function OrderForm({
  customers,
  discounts,
  action,
  submitLabel,
}: {
  customers: OrderFormCustomer[];
  discounts: OrderFormDiscount[];
  action: (prevState: FormState, formData: FormData) => Promise<FormState>;
  submitLabel: string;
}) {
  const [state, formAction, pending] = useActionState(action, { error: null });
  const [customerId, setCustomerId] = useState("");
  const [discountId, setDiscountId] = useState("");
  const [discountDollars, setDiscountDollars] = useState("0.00");
  const [shippingDollars, setShippingDollars] = useState("0.00");
  const [shippingAddress, setShippingAddress] = useState("");
  const [notes, setNotes] = useState("");
  const [items, setItems] = useState<ItemState[]>([newItem()]);
  const idPrefix = useId();
  const router = useRouter();

  function updateItem(index: number, patch: Partial<ItemState>) {
    setItems((prev) => prev.map((it, i) => (i === index ? { ...it, ...patch } : it)));
  }

  function removeItem(index: number) {
    setItems((prev) => prev.filter((_, i) => i !== index));
  }

  const dollarsToCents = (v: string) => Math.round(Number(v || "0") * 100);
  const subtotalCents = items.reduce(
    (sum, it) => sum + Number(it.quantity || "0") * dollarsToCents(it.unitPriceDollars),
    0,
  );
  const discountCents = dollarsToCents(discountDollars);
  const shippingCents = dollarsToCents(shippingDollars);
  const totalCents = Math.max(0, subtotalCents - discountCents + shippingCents);

  function buildPayload() {
    return JSON.stringify({
      customerId: customerId || null,
      status: "pending",
      discountId: discountId || null,
      discountCents,
      shippingCents,
      shippingAddress,
      notes,
      items: items.map((it) => ({
        productId: null,
        productName: it.productName,
        colourName: it.colourName || null,
        size: it.size || null,
        quantity: Number(it.quantity || "0"),
        unitPriceCents: dollarsToCents(it.unitPriceDollars),
      })),
    });
  }

  return (
    <form action={formAction} className="flex flex-col gap-6">
      <input type="hidden" name="payload" value={buildPayload()} />

      <Card className="grid gap-4 sm:grid-cols-2">
        <Field label="Customer (optional)" htmlFor={`${idPrefix}-customer`}>
          <Select
            id={`${idPrefix}-customer`}
            value={customerId}
            onChange={(e) => {
              setCustomerId(e.target.value);
            }}
          >
            <option value="">No customer on file</option>
            {customers.map((c) => (
              <option key={c.id} value={c.id}>
                {c.name} ({c.email})
              </option>
            ))}
          </Select>
        </Field>

        <Field label="Discount code (optional)" htmlFor={`${idPrefix}-discount`}>
          <Select
            id={`${idPrefix}-discount`}
            value={discountId}
            onChange={(e) => {
              setDiscountId(e.target.value);
            }}
          >
            <option value="">None</option>
            {discounts.map((d) => (
              <option key={d.id} value={d.id}>
                {d.code}
              </option>
            ))}
          </Select>
        </Field>

        <Field label="Discount amount (AUD)" htmlFor={`${idPrefix}-discount-amount`}>
          <Input
            id={`${idPrefix}-discount-amount`}
            type="number"
            step="0.01"
            min="0"
            value={discountDollars}
            onChange={(e) => {
              setDiscountDollars(e.target.value);
            }}
          />
        </Field>

        <Field label="Shipping (AUD)" htmlFor={`${idPrefix}-shipping`}>
          <Input
            id={`${idPrefix}-shipping`}
            type="number"
            step="0.01"
            min="0"
            value={shippingDollars}
            onChange={(e) => {
              setShippingDollars(e.target.value);
            }}
          />
        </Field>

        <div className="sm:col-span-2">
          <Field label="Shipping address (optional)" htmlFor={`${idPrefix}-address`}>
            <Textarea
              id={`${idPrefix}-address`}
              rows={2}
              value={shippingAddress}
              onChange={(e) => {
                setShippingAddress(e.target.value);
              }}
            />
          </Field>
        </div>

        <div className="sm:col-span-2">
          <Field label="Notes (optional)" htmlFor={`${idPrefix}-notes`} hint="Staff-facing only.">
            <Textarea
              id={`${idPrefix}-notes`}
              rows={2}
              value={notes}
              onChange={(e) => {
                setNotes(e.target.value);
              }}
            />
          </Field>
        </div>
      </Card>

      <div className="flex flex-col gap-4">
        <div className="flex items-center justify-between">
          <h2 className="display text-[20px]">Line items</h2>
          <Button
            type="button"
            variant="ghost"
            onClick={() => {
              setItems((prev) => [...prev, newItem()]);
            }}
          >
            + Add item
          </Button>
        </div>

        {items.map((item, index) => {
          const iid = `${idPrefix}-item-${String(index)}`;
          return (
            <Card key={index} className="grid gap-4 sm:grid-cols-5">
              <div className="sm:col-span-2">
                <Field label="Product name" htmlFor={`${iid}-name`}>
                  <Input
                    id={`${iid}-name`}
                    required
                    value={item.productName}
                    onChange={(e) => {
                      updateItem(index, { productName: e.target.value });
                    }}
                  />
                </Field>
              </div>
              <Field label="Colour (optional)" htmlFor={`${iid}-colour`}>
                <Input
                  id={`${iid}-colour`}
                  value={item.colourName}
                  onChange={(e) => {
                    updateItem(index, { colourName: e.target.value });
                  }}
                />
              </Field>
              <Field label="Size" htmlFor={`${iid}-size`}>
                <Select
                  id={`${iid}-size`}
                  value={item.size}
                  onChange={(e) => {
                    updateItem(index, { size: e.target.value });
                  }}
                >
                  <option value="">—</option>
                  {SIZES.map((s) => (
                    <option key={s} value={s}>
                      {s}
                    </option>
                  ))}
                </Select>
              </Field>
              <Field label="Qty" htmlFor={`${iid}-qty`}>
                <Input
                  id={`${iid}-qty`}
                  type="number"
                  min="1"
                  required
                  value={item.quantity}
                  onChange={(e) => {
                    updateItem(index, { quantity: e.target.value });
                  }}
                />
              </Field>

              <div className="sm:col-span-2">
                <Field label="Unit price (AUD)" htmlFor={`${iid}-price`}>
                  <Input
                    id={`${iid}-price`}
                    type="number"
                    step="0.01"
                    min="0"
                    required
                    value={item.unitPriceDollars}
                    onChange={(e) => {
                      updateItem(index, { unitPriceDollars: e.target.value });
                    }}
                  />
                </Field>
              </div>

              <div className="flex items-end sm:col-span-3">
                <span className="text-[13px] text-ink/50">
                  Line total:{" "}
                  <span className="font-semibold text-ink">
                    {formatCents(Number(item.quantity || "0") * dollarsToCents(item.unitPriceDollars))}
                  </span>
                </span>
              </div>

              {items.length > 1 && (
                <div className="sm:col-span-5">
                  <Button
                    type="button"
                    variant="ghost"
                    onClick={() => {
                      removeItem(index);
                    }}
                  >
                    Remove item
                  </Button>
                </div>
              )}
            </Card>
          );
        })}
      </div>

      <Card className="flex flex-col gap-1 self-end text-[14px] sm:min-w-[280px]">
        <div className="flex justify-between">
          <Label>Subtotal</Label>
          <span>{formatCents(subtotalCents)}</span>
        </div>
        <div className="flex justify-between">
          <Label>Discount</Label>
          <span>-{formatCents(discountCents)}</span>
        </div>
        <div className="flex justify-between">
          <Label>Shipping</Label>
          <span>{formatCents(shippingCents)}</span>
        </div>
        <div className="flex justify-between border-t border-ink/10 pt-1 font-semibold">
          <span>Total</span>
          <span>{formatCents(totalCents)}</span>
        </div>
      </Card>

      {state.error && (
        <p role="alert" className="text-[13px] font-semibold text-coral">
          {state.error}
        </p>
      )}

      <div className="flex gap-3">
        <Button type="submit" disabled={pending}>
          {pending ? "Saving…" : submitLabel}
        </Button>
        <Button type="button" variant="ghost" onClick={() => router.push("/orders")}>
          Cancel
        </Button>
      </div>
    </form>
  );
}
