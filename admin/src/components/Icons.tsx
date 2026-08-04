/* Same 2px-stroke, 24px-box icon convention as the storefront's Icons.tsx. */

type P = { className?: string; strokeWidth?: number };

const base = (className?: string) => ({
  viewBox: "0 0 24 24",
  fill: "none",
  stroke: "currentColor",
  strokeLinecap: "round" as const,
  strokeLinejoin: "round" as const,
  className,
  "aria-hidden": true,
});

export const IconMenu = ({ className, strokeWidth = 2 }: P) => (
  <svg {...base(className)} strokeWidth={strokeWidth}>
    <path d="M3.5 7h17M3.5 12h17M3.5 17h17" />
  </svg>
);

export const IconClose = ({ className, strokeWidth = 2 }: P) => (
  <svg {...base(className)} strokeWidth={strokeWidth}>
    <path d="M6 6l12 12M18 6L6 18" />
  </svg>
);
