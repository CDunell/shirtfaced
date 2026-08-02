import { PageShell, Prose, Section } from "@/components/PageShell";
import { SIZE_CHART } from "@/lib/products";

export const metadata = {
  title: "Size guide — Shirtfaced",
  description: "Measurements for every Shirtfaced tee. Boxy fit, sized honestly.",
};

const SIZES = Object.entries(SIZE_CHART);

export default function SizeGuidePage() {
  return (
    <PageShell
      title="size guide"
      intro="Everything is cut boxy and slightly oversized. If you want it fitted, size down. If you want it huge, you're already thinking correctly."
    >
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
              <strong>Chest</strong> — lay the tee flat, measure straight across
              one centimetre below the armhole, seam to seam. That&apos;s a
              half-chest measurement, so double it to compare against a body
              measurement.
            </p>
            <p>
              <strong>Length</strong> — from the highest point of the shoulder
              straight down to the hem.
            </p>
          </Prose>
        </Section>

        <Section heading="Between sizes?">
          <Prose>
            <p>
              Size up. These are meant to sit wide with a dropped shoulder, and
              nobody has ever complained that a tee was too comfortable.
            </p>
            <p>
              Measurements are taken flat and have a tolerance of about a
              centimetre either way, because they&apos;re cut and sewn by people
              rather than robots.
            </p>
          </Prose>
        </Section>

        <Section heading="Care">
          <Prose>
            <p>
              Cold wash, inside out, hang dry. Don&apos;t iron the print unless
              you want it to become someone else&apos;s problem.
            </p>
          </Prose>
        </Section>
      </div>
    </PageShell>
  );
}
