/**
 * Every real photography slot in DESIGN_HANDOFF.md §6 (candid kids, outdoor
 * play) needs an actual shoot — there is no photography for Curb Stamps yet
 * (see curbstamps-site/README.md). Rather than fake a photo or leave a grey
 * box, this names exactly what belongs in the slot so it reads as "shoot
 * this" rather than "broken image" — swap for a real <img>/next-image once
 * the shoot in DESIGN_HANDOFF.md §6 happens; nothing else needs to change.
 */
export function PlaceholderPhoto({
  label,
  tone = "var(--color-paper-2)",
  className,
}: {
  label: string;
  tone?: string;
  className?: string;
}) {
  return (
    <div
      className={`flex flex-col items-center justify-center gap-2 rounded-[20px] border-2 border-dashed border-ink/20 p-4 text-center ${className ?? ""}`}
      style={{ background: tone }}
    >
      <span className="text-[11px] font-extrabold tracking-wide text-ink/50 uppercase">
        Photo needed
      </span>
      <span className="text-[13px] font-bold text-ink/70">{label}</span>
    </div>
  );
}
