import { listCustomers, listDiscounts } from "@/db/store-queries";
import { OrderForm } from "@/components/OrderForm";
import { createOrderAction } from "@/app/orders/actions";

export const dynamic = "force-dynamic";

export default async function NewOrderPage() {
  const [customers, discounts] = await Promise.all([
    listCustomers(),
    listDiscounts(),
  ]);

  return (
    <div className="flex flex-col gap-6">
      <h1 className="display text-[40px]">Record order</h1>
      <p className="max-w-2xl text-[13px] text-ink/60">
        For a phone or email sale — there&apos;s no storefront checkout yet, so this is the only
        way an order reaches this system.
      </p>
      <OrderForm
        customers={customers.map((c) => ({ id: c.id, name: c.name, email: c.email }))}
        discounts={discounts.filter((d) => d.active).map((d) => ({ id: d.id, code: d.code }))}
        action={createOrderAction}
        submitLabel="Create order"
      />
    </div>
  );
}
