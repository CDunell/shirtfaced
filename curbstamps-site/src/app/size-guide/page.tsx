import { PageShell, Section, Prose } from "@/components/PageShell";

export const metadata = { title: "Size guide — Curb Stamps" };

const TODDLER = [
  { size: "2T", chest: "53cm", height: "86–92cm" },
  { size: "3T", chest: "55cm", height: "92–98cm" },
  { size: "4T", chest: "57cm", height: "98–104cm" },
  { size: "5T", chest: "59cm", height: "104–110cm" },
];

const YOUTH = [
  { size: "XS (6/7)", chest: "63cm", height: "110–122cm" },
  { size: "S (8)", chest: "67cm", height: "122–128cm" },
  { size: "M (10/12)", chest: "72cm", height: "128–147cm" },
  { size: "L (14/16)", chest: "80cm", height: "147–159cm" },
  { size: "XL (18/20)", chest: "88cm", height: "159–166cm" },
];

function SizeTable({ rows }: { rows: { size: string; chest: string; height: string }[] }) {
  return (
    <div className="mt-3 overflow-x-auto rounded-2xl border-2 border-ink/10">
      <table className="w-full min-w-[420px] text-left text-[14px]">
        <thead>
          <tr className="border-b-2 border-ink/10 text-grey-dark">
            <th className="px-4 py-3 font-bold">Size</th>
            <th className="px-4 py-3 font-bold">Chest</th>
            <th className="px-4 py-3 font-bold">Height</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((r) => (
            <tr key={r.size} className="border-b border-ink/6 last:border-0">
              <td className="px-4 py-3 font-bold">{r.size}</td>
              <td className="px-4 py-3">{r.chest}</td>
              <td className="px-4 py-3">{r.height}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export default function SizeGuidePage() {
  return (
    <PageShell title="size guide" intro="One chart, toddler to teen — measurements in cm, laid flat.">
      <Section heading="Toddler (2T–5T)">
        <SizeTable rows={TODDLER} />
      </Section>
      <Section heading="Youth (XS–XL)">
        <SizeTable rows={YOUTH} />
      </Section>
      <Section heading="Between sizes?">
        <Prose>
          <p>Size up. Everything&apos;s cut for room to grow, and a kid outgrows &quot;just right&quot; in about a school term anyway.</p>
        </Prose>
      </Section>
      <Section heading="Fit and safety">
        <Prose>
          <p>
            Hoodies for the toddler range (2T–4T) ship with no drawstrings at the hood or
            waist, in line with children&apos;s clothing drawstring safety standards
            (AS/NZS 1249) — a printed toggle or elastic does the job instead. Youth-size
            hoodies keep the drawstring.
          </p>
        </Prose>
      </Section>
    </PageShell>
  );
}
