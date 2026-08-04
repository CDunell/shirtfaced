import { notFound } from "next/navigation";
import { getProduct } from "@/db/queries";
import { ProductForm, type ProductFormValues } from "@/components/ProductForm";
import { updateProductAction } from "@/app/products/actions";
import { SIZES, type Size } from "@/db/schema";

export default async function EditProductPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;
  const product = await getProduct(id);
  if (!product) notFound();

  const initial: ProductFormValues = {
    slug: product.slug,
    name: product.name,
    category: product.category,
    art: product.art,
    priceDollars: (product.priceCents / 100).toFixed(2),
    isNew: product.isNew,
    blurb: product.blurb,
    description: product.description,
    colours: product.colours.map((c) => ({
      name: c.name,
      swatch: c.swatch,
      body: c.body,
      ink: c.ink,
      images: c.images.join("\n"),
      stock: Object.fromEntries(
        SIZES.map((size) => [
          size,
          String(c.stock.find((s) => s.size === size)?.quantity ?? 0),
        ]),
      ) as Record<Size, string>,
    })),
  };

  const action = updateProductAction.bind(null, id);

  return (
    <div className="flex flex-col gap-6">
      <h1 className="display text-[40px]">Edit product</h1>
      <ProductForm initial={initial} action={action} submitLabel="Save changes" />
    </div>
  );
}
