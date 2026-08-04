import type { ButtonHTMLAttributes, InputHTMLAttributes, LabelHTMLAttributes, SelectHTMLAttributes, TextareaHTMLAttributes } from "react";

function cx(...classes: Array<string | false | undefined>) {
  return classes.filter(Boolean).join(" ");
}

export function Button({
  variant = "primary",
  className,
  ...props
}: ButtonHTMLAttributes<HTMLButtonElement> & {
  variant?: "primary" | "ghost" | "danger";
}) {
  const base =
    "press inline-flex h-11 items-center justify-center gap-2 rounded-[var(--radius-btn)] px-5 text-[13px] font-semibold tracking-wide uppercase disabled:opacity-40 disabled:pointer-events-none";
  const variants = {
    primary: "bg-ink text-paper hover:bg-ink-soft",
    ghost: "bg-transparent text-ink hover:bg-paper-2 border border-ink/15",
    danger: "bg-coral text-ink hover:opacity-90",
  };
  return (
    <button className={cx(base, variants[variant], className)} {...props} />
  );
}

export function Label(props: LabelHTMLAttributes<HTMLLabelElement>) {
  return (
    <label
      {...props}
      className={cx(
        "block text-[12px] font-semibold tracking-wide uppercase text-ink/60",
        props.className,
      )}
    />
  );
}

const fieldClass =
  "w-full rounded-[var(--radius-input)] border border-ink/15 bg-white px-4 py-2.5 text-[15px] text-ink outline-none focus:border-ink/40";

export function Input(props: InputHTMLAttributes<HTMLInputElement>) {
  return <input {...props} className={cx(fieldClass, props.className)} />;
}

export function Textarea(props: TextareaHTMLAttributes<HTMLTextAreaElement>) {
  return (
    <textarea {...props} className={cx(fieldClass, "resize-y", props.className)} />
  );
}

export function Select(props: SelectHTMLAttributes<HTMLSelectElement>) {
  return <select {...props} className={cx(fieldClass, props.className)} />;
}

export function Field({
  label,
  htmlFor,
  children,
  hint,
}: {
  label: string;
  htmlFor: string;
  children: React.ReactNode;
  hint?: string;
}) {
  return (
    <div className="flex flex-col gap-1.5">
      <Label htmlFor={htmlFor}>{label}</Label>
      {children}
      {hint && <p className="text-[12px] text-ink/50">{hint}</p>}
    </div>
  );
}

export function Card({
  children,
  className,
}: {
  children: React.ReactNode;
  className?: string;
}) {
  return (
    <div
      className={cx(
        "rounded-[var(--radius-card)] border border-ink/10 bg-white/60 p-5",
        className,
      )}
    >
      {children}
    </div>
  );
}
