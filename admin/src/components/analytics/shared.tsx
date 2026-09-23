import Link from "next/link";

export function Stat({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <p className="text-[12px] font-semibold tracking-wide text-ink/50 uppercase">{label}</p>
      <p className="display text-[28px]">{value}</p>
    </div>
  );
}

export function NotConnected({ what, envVars }: { what: string; envVars: string[] }) {
  return (
    <p className="text-[14px] text-ink/50">
      {what} isn&apos;t connected. Set{" "}
      {envVars.map((v, i) => (
        <span key={v}>
          {i > 0 && ", "}
          <code className="rounded bg-paper-2 px-1.5 py-0.5 text-[13px]">{v}</code>
        </span>
      ))}{" "}
      to turn this on.
    </p>
  );
}

export function ReportError({ message }: { message: string }) {
  return <p className="text-[14px] text-coral">Couldn&apos;t load this: {message}</p>;
}

const RANGES = [
  { days: 7, label: "7d" },
  { days: 30, label: "30d" },
  { days: 90, label: "90d" },
];

/** Plain links, not client-side state — a server component re-fetches with
 * the new range on navigation, same as every other filter in this app. */
export function DateRangeTabs({ basePath, days }: { basePath: string; days: number }) {
  return (
    <div className="inline-flex gap-1 rounded-[var(--radius-btn)] border border-ink/15 p-1">
      {RANGES.map((r) => (
        <Link
          key={r.days}
          href={`${basePath}?days=${r.days}`}
          className={`rounded-[calc(var(--radius-btn)-4px)] px-3 py-1.5 text-[13px] font-semibold ${
            r.days === days ? "bg-ink text-paper" : "text-ink/60 hover:bg-paper-2"
          }`}
        >
          {r.label}
        </Link>
      ))}
    </div>
  );
}

export function parseDays(value: string | undefined): 7 | 30 | 90 {
  if (value === "7") return 7;
  if (value === "90") return 90;
  return 30;
}
