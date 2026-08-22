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
      className={`relative overflow-hidden border-2 border-ink/10 ${className ?? ""}`}
      style={{ background: tone }}
      role="img"
      aria-label={label}
    >
      <div className="absolute inset-x-0 bottom-0 h-[34%] bg-ink/8" />
      <div className="absolute right-[12%] top-[14%] h-8 w-8 rounded-full border-2 border-ink/35 bg-paper/40" />
      <div className="absolute left-[18%] top-[22%] h-[42%] w-[34%] rounded-[45%_45%_35%_35%] bg-ink/75" />
      <div className="absolute left-[23%] top-[12%] h-10 w-10 rounded-full bg-ink/75" />
      <div className="absolute left-[13%] top-[48%] h-2 w-[48%] -rotate-6 rounded-full bg-ink/75" />
      <div className="absolute bottom-[9%] left-[12%] right-[12%] rounded-lg bg-paper/90 px-2 py-1.5 text-center text-[9px] font-black uppercase leading-tight text-ink/65">
        {label}
      </div>
    </div>
  );
}
