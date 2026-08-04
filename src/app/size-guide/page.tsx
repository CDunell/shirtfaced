import { PageShell, Prose, Section } from "@/components/PageShell";
import { sizeGuide } from "@/lib/content-data.generated";

export const metadata = {
  title: "Size guide — Shirtfaced",
  description: "Measurements for every Shirtfaced tee. Boxy fit, sized honestly.",
};

const SIZES = Object.entries(sizeGuide.chart);

export default function SizeGuidePage() {
  return (
    <PageShell title="size guide" intro={sizeGuide.intro}>
      <div className="overflow-x-auto rounded-[20px] border border-ink/12">
        <table className="w-full min-w-[380px] text-left text-[15px]">
          <caption className="sr-only">
            Chest and length measurements by size, in centimetres
          </caption>
          <thead>
            <tr className="border-b border-ink/12 bg-paper-2">
              <th scope="col" className="px-4 py-3 font-semibold">Size</th>
              <th scope="col" className="px-4 py-3 font-semibold">Chest</th>
              <th scope="col" className="px-4 py-3 font-semibold">Length</th>
            </tr>
          </thead>
          <tbody>
            {SIZES.map(([size, m]) => (
              <tr key={size} className="border-b border-ink/8 last:border-0">
                <th scope="row" className="display px-4 py-3 text-[20px]">
                  {size}
                </th>
                <td className="px-4 py-3 tabular-nums">{m.chest}</td>
                <td className="px-4 py-3 tabular-nums">{m.length}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <div className="mt-8 flex flex-col gap-8">
        <Section heading="How to measure">
          <Prose>
            <p>
              <strong>Chest</strong> — {sizeGuide.measureChest}
            </p>
            <p>
              <strong>Length</strong> — {sizeGuide.measureLength}
            </p>
          </Prose>
        </Section>

        <Section heading="Between sizes?">
          <Prose>
            <p>{sizeGuide.betweenSizesP1}</p>
            <p>{sizeGuide.betweenSizesP2}</p>
          </Prose>
        </Section>

        <Section heading="Care">
          <Prose>
            <p>{sizeGuide.careP1}</p>
          </Prose>
        </Section>
      </div>
    </PageShell>
  );
}
