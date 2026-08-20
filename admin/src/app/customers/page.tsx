import Link from "next/link";
import { listCustomers } from "@/db/store-queries";
import { Button, Card } from "@/components/ui";

export const dynamic = "force-dynamic";

export default async function CustomersPage() {
  const customers = await listCustomers();

  return (
    <div className="flex flex-col gap-6">
      <div className="flex items-center justify-between">
        <h1 className="display text-[40px]">Customers</h1>
        <Link href="/customers/new">
          <Button type="button">+ New customer</Button>
        </Link>
      </div>

      {customers.length === 0 ? (
        <Card>
          <p className="text-ink/60">No customers yet.</p>
        </Card>
      ) : (
        <div className="flex flex-col gap-3">
          {customers.map((customer) => (
            <Link key={customer.id} href={`/customers/${customer.id}`}>
              <Card className="flex flex-wrap items-center gap-4 hover:bg-white/80">
                <div className="flex min-w-[200px] flex-1 flex-col">
                  <span className="font-semibold">{customer.name}</span>
                  <span className="text-[13px] text-ink/50">{customer.email}</span>
                </div>
                {customer.phone && (
                  <span className="text-[13px] text-ink/50">{customer.phone}</span>
                )}
                {(customer.suburb || customer.state) && (
                  <span className="text-[13px] uppercase tracking-wide text-ink/50">
                    {[customer.suburb, customer.state].filter(Boolean).join(", ")}
                  </span>
                )}
              </Card>
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}
