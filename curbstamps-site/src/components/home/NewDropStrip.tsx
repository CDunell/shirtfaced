import Link from "next/link";
import { CREATURES } from "@/lib/creatures";
import { getProduct } from "@/lib/products";
import { GarmentArt } from "@/components/GarmentArt";
import { PlaceholderPhoto } from "./PlaceholderPhoto";

export function NewDropStrip() {
  const featured = CREATURES[0];
  const tee = getProduct(`${featured.slug}-tee`)!;
  const hoodie = getProduct(`${featured.slug}-hoodie`)!;

  return (
    <section className="bg-paper">
      <div className="mx-auto max-w-5xl px-4 py-6 sm:px-6 sm:py-9">
        <div className="grid grid-cols-[0.86fr_1.14fr] overflow-hidden rounded-[18px] border-2 border-ink sm:grid-cols-4">
          <div className="flex min-h-[180px] flex-col justify-between bg-grit-pink p-4 sm:min-h-0">
            <div>
              <h2 className="display text-[24px] uppercase leading-[0.88]">new drop!</h2>
              <p className="mt-1 text-[11px] font-bold">Just landed.</p>
            </div>
            <Link href="/shop" className="press inline-flex w-fit rounded-md bg-ink px-3 py-2 text-[10px] font-black uppercase text-paper">Shop new</Link>
          </div>

          <PlaceholderPhoto label="Kid wearing the new drop" className="min-h-[180px] border-0" tone="var(--color-grit-yellow)" />

          <GarmentArt
            category="tee"
            bodyColour={tee.colours[1].body}
            art={tee.art}
            creatureName={tee.name}
            className="hidden aspect-square rounded-none border-l-2 border-ink sm:block"
          />
          <GarmentArt
            category="hoodie"
            bodyColour={hoodie.colours[0].body}
            art={hoodie.art}
            creatureName={hoodie.name}
            className="hidden aspect-square rounded-none border-l-2 border-ink sm:block"
          />
        </div>
      </div>
    </section>
  );
}
