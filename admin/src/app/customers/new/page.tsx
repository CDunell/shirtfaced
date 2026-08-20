import { CustomerForm } from "@/components/CustomerForm";
import { createCustomerAction } from "@/app/customers/actions";

export default function NewCustomerPage() {
  return (
    <div className="flex flex-col gap-6">
      <h1 className="display text-[40px]">New customer</h1>
      <CustomerForm action={createCustomerAction} submitLabel="Create customer" />
    </div>
  );
}
