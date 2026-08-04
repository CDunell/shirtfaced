import { ProductForm, emptyProduct } from "@/components/ProductForm";
import { createProductAction } from "@/app/products/actions";

export default function NewProductPage() {
  return (
    <div className="flex flex-col gap-6">
      <h1 className="display text-[40px]">New product</h1>
      <ProductForm initial={emptyProduct} action={createProductAction} submitLabel="Create product" />
    </div>
  );
}
