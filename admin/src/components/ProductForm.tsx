"use client";

import { useActionState, useId, useState } from "react";
import { useRouter } from "next/navigation";
import { CATEGORIES, SIZES, type Category, type Size } from "@/db/schema";
import type { FormState } from "@/app/products/actions";
import { Button, Card, Field, Input, Label, Select, Textarea } from "@/components/ui";

type ColourState = {
  name: string;
  swatch: string;
  body: string;
  ink: string;
  images: string; // newline-separated in the UI, split into an array on submit
  stock: Record<Size, string>;
};

export type ProductFormValues = {
  slug: string;
  name: string;
  category: Category;
  art: string;
  priceDollars: string;
  isNew: boolean;
  published: boolean;
  blurb: string;
  description: string;
  colours: ColourState[];
};

function emptyStock(): Record<Size, string> {
  return Object.fromEntries(SIZES.map((s) => [s, "0"])) as Record<Size, string>;
}

function newColour(): ColourState {
  return {
    name: "",
    swatch: "#1c1c1a",
    body: "#1c1c1a",
    ink: "#e8e2d5",
    images: "",
    stock: emptyStock(),
  };
}

export const emptyProduct: ProductFormValues = {
  slug: "",
  name: "",
  category: "tees",
  art: "",
  priceDollars: "45.00",
  isNew: false,
  published: true,
  blurb: "",
  description: "",
  colours: [newColour()],
};

export function ProductForm({
  initial,
  action,
  submitLabel,
}: {
  initial: ProductFormValues;
  action: (prevState: FormState, formData: FormData) => Promise<FormState>;
  submitLabel: string;
}) {
  const [state, formAction, pending] = useActionState(action, { error: null });
  const [product, setProduct] = useState(initial);
  const idPrefix = useId();
  const router = useRouter();

  function updateColour(index: number, patch: Partial<ColourState>) {
    setProduct((p) => ({
      ...p,
      colours: p.colours.map((c, i) => (i === index ? { ...c, ...patch } : c)),
    }));
  }

  function updateStock(index: number, size: Size, value: string) {
    setProduct((p) => ({
      ...p,
      colours: p.colours.map((c, i) =>
        i === index ? { ...c, stock: { ...c.stock, [size]: value } } : c,
      ),
    }));
  }

  function removeColour(index: number) {
    setProduct((p) => ({ ...p, colours: p.colours.filter((_, i) => i !== index) }));
  }

  function buildPayload() {
    return JSON.stringify({
      slug: product.slug,
      name: product.name,
      category: product.category,
      art: product.art,
      priceCents: Math.round(Number(product.priceDollars || "0") * 100),
      isNew: product.isNew,
      published: product.published,
      blurb: product.blurb,
      description: product.description,
      colours: product.colours.map((c) => ({
        name: c.name,
        swatch: c.swatch,
        body: c.body,
        ink: c.ink,
        images: c.images
          .split("\n")
          .map((s) => s.trim())
          .filter(Boolean),
        stock: Object.fromEntries(
          Object.entries(c.stock).map(([size, qty]) => [size, Number(qty || "0")]),
        ),
      })),
    });
  }

  return (
    <form action={formAction} className="flex flex-col gap-6">
      <input type="hidden" name="payload" value={buildPayload()} />

      <Card className="grid gap-4 sm:grid-cols-2">
        <Field label="Name" htmlFor={`${idPrefix}-name`}>
          <Input
            id={`${idPrefix}-name`}
            required
            value={product.name}
            onChange={(e) => setProduct((p) => ({ ...p, name: e.target.value }))}
          />
        </Field>

        <Field label="Slug" htmlFor={`${idPrefix}-slug`} hint="Lowercase, hyphenated, used in the product URL">
          <Input
            id={`${idPrefix}-slug`}
            required
            pattern="[a-z0-9-]+"
            value={product.slug}
            onChange={(e) => setProduct((p) => ({ ...p, slug: e.target.value }))}
          />
        </Field>

        <Field label="Category" htmlFor={`${idPrefix}-category`}>
          <Select
            id={`${idPrefix}-category`}
            value={product.category}
            onChange={(e) =>
              setProduct((p) => ({ ...p, category: e.target.value as Category }))
            }
          >
            {CATEGORIES.map((c) => (
              <option key={c} value={c}>
                {c}
              </option>
            ))}
          </Select>
        </Field>

        <Field label="Art key" htmlFor={`${idPrefix}-art`} hint="Maps to a renderer in the storefront's TeeArt.tsx">
          <Input
            id={`${idPrefix}-art`}
            required
            value={product.art}
            onChange={(e) => setProduct((p) => ({ ...p, art: e.target.value }))}
          />
        </Field>

        <Field label="Price (AUD)" htmlFor={`${idPrefix}-price`}>
          <Input
            id={`${idPrefix}-price`}
            type="number"
            step="0.01"
            min="0"
            required
            value={product.priceDollars}
            onChange={(e) => setProduct((p) => ({ ...p, priceDollars: e.target.value }))}
          />
        </Field>

        <div className="flex items-end gap-5 pb-2.5">
          <label className="flex items-center gap-2 text-[13px] font-semibold uppercase tracking-wide text-ink/70">
            <input
              type="checkbox"
              checked={product.isNew}
              onChange={(e) => setProduct((p) => ({ ...p, isNew: e.target.checked }))}
              className="h-4 w-4 accent-lime"
            />
            Mark as new
          </label>
          <label className="flex items-center gap-2 text-[13px] font-semibold uppercase tracking-wide text-ink/70">
            <input
              type="checkbox"
              checked={product.published}
              onChange={(e) => setProduct((p) => ({ ...p, published: e.target.checked }))}
              className="h-4 w-4 accent-lime"
            />
            Published — live on the storefront
          </label>
        </div>

        <Field label="Blurb" htmlFor={`${idPrefix}-blurb`} hint="One dry, Australian line">
          <Input
            id={`${idPrefix}-blurb`}
            required
            value={product.blurb}
            onChange={(e) => setProduct((p) => ({ ...p, blurb: e.target.value }))}
          />
        </Field>

        <div className="sm:col-span-2">
          <Field label="Description" htmlFor={`${idPrefix}-description`}>
            <Textarea
              id={`${idPrefix}-description`}
              required
              rows={4}
              value={product.description}
              onChange={(e) => setProduct((p) => ({ ...p, description: e.target.value }))}
            />
          </Field>
        </div>
      </Card>

      <div className="flex flex-col gap-4">
        <div className="flex items-center justify-between">
          <h2 className="display text-[20px]">Colourways &amp; stock</h2>
          <Button
            type="button"
            variant="ghost"
            onClick={() => setProduct((p) => ({ ...p, colours: [...p.colours, newColour()] }))}
          >
            + Add colourway
          </Button>
        </div>

        {product.colours.map((colour, index) => {
          const cid = `${idPrefix}-colour-${index}`;
          return (
            <Card key={index} className="flex flex-col gap-4">
              <div className="grid gap-4 sm:grid-cols-4">
                <div className="sm:col-span-2">
                  <Field label="Colour name" htmlFor={`${cid}-name`}>
                    <Input
                      id={`${cid}-name`}
                      required
                      value={colour.name}
                      onChange={(e) => updateColour(index, { name: e.target.value })}
                    />
                  </Field>
                </div>
                <Field label="Swatch" htmlFor={`${cid}-swatch`}>
                  <Input
                    id={`${cid}-swatch`}
                    type="color"
                    className="h-11 p-1"
                    value={colour.swatch}
                    onChange={(e) => updateColour(index, { swatch: e.target.value })}
                  />
                </Field>
                <Field label="Body" htmlFor={`${cid}-body`}>
                  <Input
                    id={`${cid}-body`}
                    type="color"
                    className="h-11 p-1"
                    value={colour.body}
                    onChange={(e) => updateColour(index, { body: e.target.value })}
                  />
                </Field>
                <Field label="Ink" htmlFor={`${cid}-ink`}>
                  <Input
                    id={`${cid}-ink`}
                    type="color"
                    className="h-11 p-1"
                    value={colour.ink}
                    onChange={(e) => updateColour(index, { ink: e.target.value })}
                  />
                </Field>
              </div>

              <Field
                label="Images"
                htmlFor={`${cid}-images`}
                hint="One image URL per line — real photography for this colourway"
              >
                <Textarea
                  id={`${cid}-images`}
                  rows={2}
                  value={colour.images}
                  onChange={(e) => updateColour(index, { images: e.target.value })}
                />
              </Field>

              <div>
                <Label htmlFor={`${cid}-stock`}>Stock by size</Label>
                <div id={`${cid}-stock`} className="mt-1.5 grid grid-cols-5 gap-2">
                  {SIZES.map((size) => (
                    <div key={size} className="flex flex-col gap-1">
                      <span className="text-center text-[11px] font-semibold text-ink/50">
                        {size}
                      </span>
                      <Input
                        type="number"
                        min="0"
                        value={colour.stock[size]}
                        onChange={(e) => updateStock(index, size, e.target.value)}
                      />
                    </div>
                  ))}
                </div>
              </div>

              {product.colours.length > 1 && (
                <Button
                  type="button"
                  variant="ghost"
                  className="self-start"
                  onClick={() => removeColour(index)}
                >
                  Remove colourway
                </Button>
              )}
            </Card>
          );
        })}
      </div>

      {state.error && (
        <p role="alert" className="text-[13px] font-semibold text-coral">
          {state.error}
        </p>
      )}

      <div className="flex gap-3">
        <Button type="submit" disabled={pending}>
          {pending ? "Saving…" : submitLabel}
        </Button>
        <Button type="button" variant="ghost" onClick={() => router.push("/products")}>
          Cancel
        </Button>
      </div>
    </form>
  );
}
