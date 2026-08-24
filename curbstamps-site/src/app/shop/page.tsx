import Link from "next/link";
import { getProduct, withPrintifyData, designsForCategory, CATEGORY_LABEL, CREATURES, type Category } from "@/lib/products";
import { GarmentArt } from "@/components/GarmentArt";
import { money } from "@/lib/money";

export const metadata = { title: "Shop — Curb Stamps" };

const CATEGORIES = Object.keys(CATEGORY_LABEL) as Category[];

export default async function ShopPage() {
  const defaultCreature = CREATURES[0];
  const [cards, designCount] = await Promise.all([
    Promise.all(
      CATEGORIES.map(async (category) => {
        const raw = getProduct(`${defaultCreature.slug}-${category}`)!;
        return withPrintifyData(raw);
      })
    ),
    // Every category was built from the same creature roster this session,
    // so any one of them gives the real, currently-available count (e.g.
    // 43, not CREATURES.length's 44 — "dreg" is in the roster but was
    // dropped from the actual Printify catalog).
    designsForCategory("tee").then((d) => d.length),
  ]);

  return (
    <div className="mx-auto max-w-5xl px-4 pt-4 pb-16 sm:px-6">
      <h1 className="display text-[13vw] leading-[0.9] sm:text-[54px]">shop</h1>
      <p className="mt-3 max-w-[46ch] text-[15px] text-ink/70">
        Pick a garment, then pick your favourite of {designCount} creatures — every design comes on every garment.
      </p>

      <div className="mt-6 grid grid-cols-2 gap-x-4 gap-y-8 sm:grid-cols-4">
        {cards.map((product) => {
          const colour = product.colours[0];
          return (
            <Link key={product.category} href={`/products/${product.category}`} className="press group block">
              <GarmentArt
                category={product.category}
                bodyColour={colour.body}
                art={product.art}
                artDark={product.artDark}
                creatureName={product.name}
                photoSrc={product.photos?.[colour.name]}
                className="aspect-square rounded-card"
              />
              <p className="mt-3 text-[15px] font-extrabold">{CATEGORY_LABEL[product.category]}</p>
              <p className="text-[13px] text-grey-dark">{designCount} designs to choose from</p>
              <p className="mt-1 text-[14px] font-bold">{money(product.price)}</p>
            </Link>
          );
        })}
      </div>
    </div>
  );
}
