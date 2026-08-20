import { notFound } from "next/navigation";
import Link from "next/link";
import { getCustomer, orderReference } from "@/db/store-queries";
import { CustomerForm } from "@/components/CustomerForm";
import { DeleteCustomerButton } from "@/components/DeleteCustomerButton";
import { updateCustomerAction } from "@/app/customers/actions";
import { Card } from "@/components/ui";
import { formatCents } from "@/lib/money";

export default async function EditCustomerPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;
  const customer = await getCustomer(id);
  if (!customer) notFound();

  const initial = {
    email: customer.email,
    name: customer.name,
    phone: customer.phone ?? "",
    addressLine1: customer.addressLine1 ?? "",
    addressLine2: customer.addressLine2 ?? "",
    suburb: customer.suburb ?? "",
    state: customer.state ?? "",
    postcode: customer.postcode ?? "",
    country: customer.country,
    notes: customer.notes ?? "",
  };

  const action = updateCustomerAction.bind(null, id);

  return (
    <div className="flex flex-col gap-8">
      <div className="flex items-center justify-between">
        <h1 className="display text-[40px]">Edit customer</h1>
        <DeleteCustomerButton id={customer.id} name={customer.name} />
      </div>

      <CustomerForm initial={initial} action={action} submitLabel="Save changes" />

      <div className="flex flex-col gap-3">
        <h2 className="display text-[24px]">Orders</h2>
        {customer.orders.length === 0 ? (
          <Card>
            <p className="text-ink/60">No orders yet.</p>
          </Card>
        ) : (
          <div className="flex flex-col gap-3">
            {customer.orders.map((order) => (
              <Link key={order.id} href={`/orders/${order.id}`}>
                <Card className="flex flex-wrap items-center gap-4 hover:bg-white/80">
                  <span className="font-mono text-[13px]">{orderReference(order.orderSeq)}</span>
                  <span className="text-[13px] uppercase tracking-wide text-ink/50">
                    {order.status}
                  </span>
                  <span className="font-semibold">{formatCents(order.totalCents)}</span>
                </Card>
              </Link>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
