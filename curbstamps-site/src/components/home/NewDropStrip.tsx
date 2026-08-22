import { CREATURES } from "@/lib/creatures";
import { getProduct } from "@/lib/products";
import { GarmentArt } from "@/components/GarmentArt";
import { PlaceholderPhoto } from "./PlaceholderPhoto";

/** Section C — "NEW DROP" (DESIGN_HANDOFF.md §4.C). Mixed photo/product
 * strip directly under the creature chooser. */
export function NewDropStrip() {
  const featured = CREATURES[0];
  const tee = getProduct(`${featured.slug}-tee`)!;
  const hoodie = getProduct(`${featured.slug}-hoodie`)!;

  return (
    <section className="bg-paper">
      <div className="mx-auto max-w-5xl px-4 py-8 sm:px-6">
        <div className="mb-5 inline-flex flex-col gap-0.5 rounded-2xl bg-grit-yellow px-4 py-2">
          <span className="display text-[18px] leading-none">new drop!</span>
          <span className="text-[11px] font-bold text-ink/70">Just landed. Shop new →</span>
        </div>
        <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
          <PlaceholderPhoto label="Candid kid laughing outdoors" className="aspect-[3/4]" tone="var(--color-grit-blue)" />
          <GarmentArt
            category="tee"
            bodyColour={tee.colours[1].body}
            art={tee.art}
            artDark={tee.artDark}
            creatureName={tee.name}
            className="aspect-[3/4] rounded-[20px]"
          />
          <GarmentArt
            category="hoodie"
            bodyColour={hoodie.colours[0].body}
            art={hoodie.art}
            artDark={hoodie.artDark}
            creatureName={hoodie.name}
            className="aspect-[3/4] rounded-[20px]"
          />
          <PlaceholderPhoto label="Candid kid running/playing" className="aspect-[3/4]" tone="var(--color-grit-pink)" />
        </div>
      </div>
    </section>
  );
}
