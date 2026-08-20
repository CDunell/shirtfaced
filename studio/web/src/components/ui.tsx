/**
 * Shared Tailwind primitives, replacing Base Web component-by-component.
 *
 * Ported in spirit from admin/src/components/ui.tsx (Button, Input, Textarea,
 * Select, Field, Card) and extended with the additional primitives Studio's
 * benches use that Admin's simpler forms never needed: Checkbox, Notification,
 * Tag, ProgressBar, Spinner, Table, and the Typography scale. Every bench still
 * on baseui migrates onto these one file at a time -- this file is the target,
 * not a finished migration.
 *
 * Prop shapes intentionally echo baseui's where that costs nothing (variant
 * names, a `kind` prop on Tag/Notification) so each bench's own migration is a
 * near-mechanical import swap rather than a redesign. Select is the one
 * deliberate exception: baseui's Select returns an array of {id,label} option
 * objects even in single-select mode, which no native element does -- this
 * Select takes and returns a plain string value, and each bench's migration
 * updates its own state shape to match rather than this component faking
 * baseui's shape back.
 */
import {
  createContext,
  useContext,
  useEffect,
  useId,
  useState,
  type ButtonHTMLAttributes,
  type InputHTMLAttributes,
  type LabelHTMLAttributes,
  type ReactNode,
  type SelectHTMLAttributes,
  type TextareaHTMLAttributes,
} from "react";

export function cx(...classes: Array<string | false | undefined | null>): string {
  return classes.filter(Boolean).join(" ");
}

// ---------------------------------------------------------------------------
// Button
// ---------------------------------------------------------------------------

export type ButtonVariant = "primary" | "secondary" | "ghost" | "danger";
export type ButtonSize = "default" | "compact";

export function Button({
  variant = "primary",
  size = "default",
  className,
  ...props
}: ButtonHTMLAttributes<HTMLButtonElement> & {
  variant?: ButtonVariant;
  size?: ButtonSize;
}): React.JSX.Element {
  const base =
    "press inline-flex items-center justify-center gap-2 rounded-[var(--radius-btn)] font-semibold tracking-wide uppercase disabled:opacity-40 disabled:pointer-events-none";
  const sizes: Record<ButtonSize, string> = {
    default: "h-11 px-5 text-[13px]",
    compact: "h-9 px-4 text-[12px]",
  };
  const variants: Record<ButtonVariant, string> = {
    primary: "bg-ink text-paper hover:bg-ink-soft",
    secondary: "bg-paper-2 text-ink hover:bg-paper",
    ghost: "bg-transparent text-ink border border-ink/15 hover:bg-paper-2",
    danger: "bg-coral text-ink hover:opacity-90",
  };
  return (
    <button className={cx(base, sizes[size], variants[variant], className)} {...props} />
  );
}

// ---------------------------------------------------------------------------
// Form fields
// ---------------------------------------------------------------------------

export function Label(props: LabelHTMLAttributes<HTMLLabelElement>): React.JSX.Element {
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
  "w-full rounded-[var(--radius-input)] border border-ink/15 bg-white px-4 py-2.5 text-[15px] text-ink outline-none focus:border-ink/40 disabled:opacity-50";

export function Input(props: InputHTMLAttributes<HTMLInputElement>): React.JSX.Element {
  return <input {...props} className={cx(fieldClass, props.className)} />;
}

export function Textarea(
  props: TextareaHTMLAttributes<HTMLTextAreaElement>,
): React.JSX.Element {
  return <textarea {...props} className={cx(fieldClass, "resize-y", props.className)} />;
}

export interface SelectOption {
  value: string;
  label: string;
}

/** Plain string value in, plain string value out -- see file header. */
export function Select({
  options,
  value,
  onChange,
  placeholder,
  className,
  ...rest
}: Omit<SelectHTMLAttributes<HTMLSelectElement>, "onChange" | "value"> & {
  options: SelectOption[];
  value: string;
  onChange: (value: string) => void;
  placeholder?: string;
}): React.JSX.Element {
  return (
    <select
      {...rest}
      value={value}
      onChange={(event) => {
        onChange(event.target.value);
      }}
      className={cx(fieldClass, "appearance-none", className)}
    >
      {placeholder ? (
        <option value="" disabled={value !== ""}>
          {placeholder}
        </option>
      ) : null}
      {options.map((option) => (
        <option key={option.value} value={option.value}>
          {option.label}
        </option>
      ))}
    </select>
  );
}

export function Checkbox({
  checked,
  onChange,
  children,
  className,
}: {
  checked: boolean;
  onChange: (checked: boolean) => void;
  children?: ReactNode;
  className?: string;
}): React.JSX.Element {
  return (
    <label className={cx("inline-flex cursor-pointer items-center gap-2 text-[14px] text-ink", className)}>
      <input
        type="checkbox"
        checked={checked}
        onChange={(event) => {
          onChange(event.target.checked);
        }}
        className="h-[18px] w-[18px] rounded-[6px] border border-ink/25 accent-ink"
      />
      {children}
    </label>
  );
}

export function FormControl({
  label,
  caption,
  children,
}: {
  label: string;
  caption?: ReactNode;
  children: ReactNode;
}): React.JSX.Element {
  const id = useId();
  return (
    <div className="flex flex-col gap-1.5">
      <Label htmlFor={id}>{label}</Label>
      {children}
      {caption ? <p className="text-[12px] text-ink/50">{caption}</p> : null}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Surfaces
// ---------------------------------------------------------------------------

export function Card({
  children,
  className,
}: {
  children: ReactNode;
  className?: string;
}): React.JSX.Element {
  return (
    <div className={cx("rounded-[var(--radius-card)] border border-ink/10 bg-white/60 p-5 dark:bg-white/5", className)}>
      {children}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Notification
// ---------------------------------------------------------------------------

export type NotificationKind = "info" | "positive" | "negative" | "warning";

const NOTIFICATION_STYLES: Record<NotificationKind, string> = {
  info: "bg-paper-2 text-ink",
  positive: "bg-lime text-ink",
  negative: "bg-coral text-ink",
  warning: "bg-cream text-ink",
};

export function Notification({
  kind = "info",
  children,
  className,
}: {
  kind?: NotificationKind;
  children: ReactNode;
  className?: string;
}): React.JSX.Element {
  return (
    <div
      role={kind === "negative" ? "alert" : "status"}
      className={cx(
        "rounded-[var(--radius-input)] px-4 py-3 text-[14px] font-medium",
        NOTIFICATION_STYLES[kind],
        className,
      )}
    >
      {children}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Tag
// ---------------------------------------------------------------------------

export type TagKind = "neutral" | "positive" | "negative" | "warning" | "accent";

const TAG_STYLES: Record<TagKind, string> = {
  neutral: "bg-paper-2 text-ink/70",
  positive: "bg-lime text-ink",
  negative: "bg-coral text-ink",
  warning: "bg-cream text-ink",
  accent: "bg-ink text-paper",
};

export function Tag({
  kind = "neutral",
  children,
  className,
}: {
  kind?: TagKind;
  children: ReactNode;
  className?: string;
}): React.JSX.Element {
  return (
    <span
      className={cx(
        "inline-block rounded-[8px] px-2 py-[3px] text-[11px] font-bold tracking-wide uppercase whitespace-nowrap",
        TAG_STYLES[kind],
        className,
      )}
    >
      {children}
    </span>
  );
}

// ---------------------------------------------------------------------------
// ProgressBar / Spinner
// ---------------------------------------------------------------------------

export function ProgressBar({
  value,
  className,
}: {
  /** 0-100 */
  value: number;
  className?: string;
}): React.JSX.Element {
  const clamped = Math.max(0, Math.min(100, value));
  return (
    <div
      role="progressbar"
      aria-valuenow={clamped}
      aria-valuemin={0}
      aria-valuemax={100}
      className={cx("h-2 w-full overflow-hidden rounded-full bg-paper-2", className)}
    >
      <div
        className="h-full rounded-full bg-ink transition-[width] duration-300 ease-out"
        style={{ width: `${clamped}%` }}
      />
    </div>
  );
}

export function Spinner({ className }: { className?: string }): React.JSX.Element {
  return (
    <span
      role="status"
      aria-label="Loading"
      className={cx(
        "inline-block h-5 w-5 animate-spin rounded-full border-2 border-ink/20 border-t-ink",
        className,
      )}
    />
  );
}

// ---------------------------------------------------------------------------
// Table
// ---------------------------------------------------------------------------

export function Table({
  columns,
  rows,
}: {
  columns: string[];
  rows: ReactNode[][];
}): React.JSX.Element {
  return (
    <div className="overflow-x-auto rounded-[var(--radius-card)] border border-ink/10">
      <table className="w-full border-collapse text-left text-[14px]">
        <thead>
          <tr className="border-b border-ink/10">
            {columns.map((column) => (
              <th
                key={column}
                className="px-4 py-2.5 text-[11px] font-bold tracking-wide text-ink/50 uppercase"
              >
                {column}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((row, rowIndex) => (
            // Rows are positional data snapshots, not identity-bearing records.
            <tr key={rowIndex} className="border-b border-ink/5 last:border-0">
              {row.map((cell, cellIndex) => (
                <td key={cellIndex} className="px-4 py-2.5 align-top">
                  {cell}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Typography
//
// Base Web names these by role (HeadingSmall, LabelSmall, ParagraphXSmall,
// MonoLabelSmall...). Kept as named components rather than raw className
// strings so a bench migration reads the same shape it already has.
// ---------------------------------------------------------------------------

function typographyComponent(tag: "h2" | "h3" | "p" | "span", className: string) {
  return function TypographyComponent({
    children,
    className: extra,
  }: {
    children: ReactNode;
    className?: string;
  }): React.JSX.Element {
    const Tag = tag;
    return <Tag className={cx(className, extra)}>{children}</Tag>;
  };
}

export const HeadingSmall = typographyComponent("h2", "text-[20px] font-bold text-ink");
export const LabelSmall = typographyComponent(
  "span",
  "text-[13px] font-semibold tracking-wide text-ink",
);
export const LabelXSmall = typographyComponent(
  "span",
  "text-[11px] font-semibold tracking-wide uppercase text-ink/60",
);
export const ParagraphSmall = typographyComponent("p", "text-[14px] leading-relaxed text-ink/80");
export const ParagraphXSmall = typographyComponent(
  "p",
  "text-[12px] leading-relaxed text-ink/60",
);
export const MonoLabelSmall = typographyComponent(
  "span",
  "font-mono text-[13px] text-ink/70",
);
export const MonoLabelXSmall = typographyComponent(
  "span",
  "font-mono text-[11px] text-ink/60",
);

// ---------------------------------------------------------------------------
// Theme context
//
// Replaces Base Web's `useStyletron` theme access for the handful of call
// sites that read theme colours directly rather than through a component.
// Most `useStyletron` usage disappears entirely once its call site is plain
// Tailwind classes; this remains only for genuinely dynamic values (e.g. a
// colour chosen by data, not by variant).
// ---------------------------------------------------------------------------

export type ThemeMode = "light" | "dark";

const ThemeModeContext = createContext<ThemeMode>("light");

export function ThemeModeProvider({
  mode,
  children,
}: {
  mode: ThemeMode;
  children: ReactNode;
}): React.JSX.Element {
  return <ThemeModeContext.Provider value={mode}>{children}</ThemeModeContext.Provider>;
}

export function useThemeMode(): ThemeMode {
  return useContext(ThemeModeContext);
}

/** Mirrors the current theme mode onto `<html class="dark">` for Tailwind's `dark:` variant. */
export function useSyncDarkClass(mode: ThemeMode): void {
  useEffect(() => {
    document.documentElement.classList.toggle("dark", mode === "dark");
  }, [mode]);
}

// Re-exported so call sites migrating off `useState` boilerplate for simple
// open/close panels have one place to reach for it. Not a baseui port -- new,
// because several benches hand-rolled this same pattern independently.
export function useDisclosureState(initial = false): [boolean, () => void] {
  const [open, setOpen] = useState(initial);
  return [open, () => { setOpen((value) => !value); }];
}
