import { listDiscounts } from "@/db/store-queries";
import { DiscountForm } from "@/components/DiscountForm";
import { DeleteDiscountButton } from "@/components/DeleteDiscountButton";
import { createDiscountAction, updateDiscountAction } from "@/app/discounts/actions";
import { Card } from "@/components/ui";
import { formatCents } from "@/lib/money";

export const dynamic = "force-dynamic";

export default async function DiscountsPage() {
  const discounts = await listDiscounts();

  return (
    <div className="flex flex-col gap-8">
      <h1 className="display text-[40px]">Discounts</h1>

      <div className="flex flex-col gap-4">
        {discounts.length === 0 && (
          <Card>
            <p className="text-ink/60">No discount codes yet.</p>
          </Card>
        )}

        {discounts.map((discount) => (
          <Card key={discount.id} className="flex flex-col gap-4">
            <div className="flex flex-wrap items-center gap-3">
              <span className="font-mono text-[15px] font-semibold">{discount.code}</span>
              <span className="text-[13px] text-ink/50">
                {discount.type === "percent"
                  ? `${String(discount.value)}% off`
                  : `${formatCents(discount.value)} off`}
              </span>
              <span
                className={`rounded-full px-2 py-0.5 text-[10px] font-bold uppercase ${
                  discount.active ? "bg-lime" : "bg-paper-2 text-ink/50"
                }`}
              >
                {discount.active ? "Active" : "Inactive"}
              </span>
              {discount.usageLimit !== null && (
                <span className="text-[13px] text-ink/50">
                  {discount.timesUsed} / {discount.usageLimit} used
                </span>
              )}
            </div>
            <DiscountForm
              initial={{
                code: discount.code,
                type: discount.type,
                value: String(discount.value),
                active: discount.active,
                startsAt: discount.startsAt?.toISOString() ?? "",
                expiresAt: discount.expiresAt?.toISOString() ?? "",
                usageLimit: discount.usageLimit === null ? "" : String(discount.usageLimit),
              }}
              action={updateDiscountAction.bind(null, discount.id)}
              submitLabel="Save changes"
            />
            <DeleteDiscountButton id={discount.id} code={discount.code} />
          </Card>
        ))}
      </div>

      <div className="flex flex-col gap-3">
        <h2 className="display text-[24px]">New discount code</h2>
        <Card>
          <DiscountForm action={createDiscountAction} submitLabel="Create discount" />
        </Card>
      </div>
    </div>
  );
}
