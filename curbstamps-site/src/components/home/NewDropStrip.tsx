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
        <div className="no-scrollbar flex overflow-x-auto border-y border-ink/15 sm:grid sm:grid-cols-5 sm:overflow-hidden sm:rounded-[16px] sm:border-2 sm:border-ink">
          <div className="flex min-h-[142px] w-[124px] shrink-0 flex-col justify-between bg-grit-pink p-3.5 sm:min-h-[190px] sm:w-auto">
            <div>
              <h2 className="display text-[21px] uppercase leading-[0.88]">new drop!</h2>
              <p className="mt-1 text-[10px] font-bold">Just landed.</p>
            </div>
            <Link href="/shop" className="press inline-flex w-fit rounded-md bg-ink px-3 py-2 text-[9px] font-black uppercase text-paper">Shop new</Link>
          </div>

          <PlaceholderPhoto label="Kid wearing the new drop" className="min-h-[142px] w-[132px] shrink-0 rounded-none border-0 border-l border-ink/15 sm:min-h-[190px] sm:w-auto" tone="var(--color-grit-yellow)" />

          <GarmentArt
            category="tee"
            bodyColour={tee.colours[1].body}
            art={tee.art}
            artDark={tee.artDark}
            creatureName={tee.name}
            className="min-h-[142px] w-[132px] shrink-0 rounded-none border-l border-ink/15 sm:min-h-[190px] sm:w-auto"
          />
          <GarmentArt
            category="hoodie"
            bodyColour={hoodie.colours[0].body}
            art={hoodie.art}
            artDark={hoodie.artDark}
            creatureName={hoodie.name}
            className="min-h-[142px] w-[132px] shrink-0 rounded-none border-l border-ink/15 sm:min-h-[190px] sm:w-auto"
          />
          <PlaceholderPhoto label="Kid wearing a Curb Stamps tee" className="min-h-[142px] w-[132px] shrink-0 rounded-none border-0 border-l border-ink/15 sm:min-h-[190px] sm:w-auto" tone="var(--color-grit-blue)" />
        </div>
      </div>
    </section>
  );
}
