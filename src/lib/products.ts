export type Product = {
  slug: string;
  name: string;
  price: number;
  color: string;
  swatch: string;
  description: string;
  sizes: string[];
};

export const products: Product[] = [
  {
    slug: "classic-tee-black",
    name: "Classic Tee — Black",
    price: 28,
    color: "Black",
    swatch: "#18181b",
    description:
      "Heavyweight 100% cotton tee with a boxy fit. The one you reach for every day.",
    sizes: ["S", "M", "L", "XL", "XXL"],
  },
  {
    slug: "classic-tee-white",
    name: "Classic Tee — White",
    price: 28,
    color: "White",
    swatch: "#f4f4f5",
    description:
      "Heavyweight 100% cotton tee with a boxy fit. The one you reach for every day.",
    sizes: ["S", "M", "L", "XL", "XXL"],
  },
  {
    slug: "washed-tee-clay",
    name: "Washed Tee — Clay",
    price: 32,
    color: "Clay",
    swatch: "#b45f3d",
    description:
      "Garment-dyed and stone-washed for a broken-in feel right out of the bag.",
    sizes: ["S", "M", "L", "XL"],
  },
  {
    slug: "washed-tee-moss",
    name: "Washed Tee — Moss",
    price: 32,
    color: "Moss",
    swatch: "#4b5d3a",
    description:
      "Garment-dyed and stone-washed for a broken-in feel right out of the bag.",
    sizes: ["S", "M", "L", "XL"],
  },
  {
    slug: "logo-tee-navy",
    name: "Logo Tee — Navy",
    price: 30,
    color: "Navy",
    swatch: "#1e2a4a",
    description:
      "Small chest-print Shirtfaced wordmark. Regular fit, midweight cotton.",
    sizes: ["S", "M", "L", "XL", "XXL"],
  },
  {
    slug: "pocket-tee-heather-grey",
    name: "Pocket Tee — Heather Grey",
    price: 30,
    color: "Heather Grey",
    swatch: "#9ca3af",
    description: "A no-frills pocket tee. Soft hand, relaxed drape.",
    sizes: ["S", "M", "L", "XL"],
  },
];

export function getProduct(slug: string) {
  return products.find((p) => p.slug === slug);
}
