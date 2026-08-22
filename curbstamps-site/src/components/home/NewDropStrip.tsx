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
      <div className="mx-auto max-w-5xl py-0 sm:px-6 sm:py-7">
        <div className="grid grid-cols-2 overflow-hidden border-y border-ink/15 sm:grid-cols-5 sm:rounded-[16px] sm:border-2 sm:border-ink">
          <div className="flex min-h-[154px] flex-col justify-between bg-grit-pink p-4 sm:min-h-[190px]">
            <div>
              <h2 className="display text-[21px] uppercase leading-[0.88]">new drop!</h2>
              <p className="mt-1 text-[12px] font-bold">Just landed.</p>
            </div>
            <Link href="/shop" className="press inline-flex min-h-11 w-fit items-center rounded-md bg-ink px-3 py-2 text-[11px] font-black uppercase text-paper">Shop new</Link>
          </div>

          <PlaceholderPhoto label="Kid wearing the new drop" className="min-h-[154px] rounded-none border-0 border-l border-ink/15 sm:min-h-[190px]" tone="var(--color-grit-yellow)" />

          <GarmentArt
            category="tee"
            bodyColour={tee.colours[1].body}
            art={tee.art}
            artDark={tee.artDark}
            creatureName={tee.name}
            className="min-h-[154px] rounded-none border-l-0 border-t border-ink/15 sm:min-h-[190px] sm:border-l sm:border-t-0"
          />
          <GarmentArt
            category="hoodie"
            bodyColour={hoodie.colours[0].body}
            art={hoodie.art}
            artDark={hoodie.artDark}
            creatureName={hoodie.name}
            className="min-h-[154px] rounded-none border-l border-t border-ink/15 sm:min-h-[190px] sm:border-t-0"
          />
          <PlaceholderPhoto label="Kid wearing a Curb Stamps tee" className="col-span-2 min-h-[170px] rounded-none border-0 border-t border-ink/15 sm:col-span-1 sm:min-h-[190px] sm:border-l sm:border-t-0" tone="var(--color-grit-blue)" />
        </div>
      </div>
    </section>
  );
}
