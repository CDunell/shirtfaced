/* Icon set — 2px stroke, rounded joins, consistent 24px box. Never decorative. */

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

export const IconSearch = ({ className, strokeWidth = 2 }: P) => (
  <svg {...base(className)} strokeWidth={strokeWidth}>
    <circle cx="11" cy="11" r="6.5" />
    <path d="m16 16 4.5 4.5" />
  </svg>
);

export const IconBag = ({ className, strokeWidth = 2 }: P) => (
  <svg {...base(className)} strokeWidth={strokeWidth}>
    <path d="M4.5 7.5h15l-1 12.5a1.5 1.5 0 0 1-1.5 1.4H7a1.5 1.5 0 0 1-1.5-1.4z" />
    <path d="M8.5 10V6.5a3.5 3.5 0 0 1 7 0V10" />
  </svg>
);

export const IconSmiley = ({ className, strokeWidth = 2 }: P) => (
  <svg {...base(className)} strokeWidth={strokeWidth}>
    <circle cx="12" cy="12" r="8.5" />
    <path d="M8.5 13.5a4.5 4.5 0 0 0 7 0" />
    <circle cx="9.3" cy="9.8" r="1" fill="currentColor" stroke="none" />
    <circle cx="14.7" cy="9.8" r="1" fill="currentColor" stroke="none" />
  </svg>
);

export const IconBolt = ({ className, strokeWidth = 2 }: P) => (
  <svg {...base(className)} strokeWidth={strokeWidth}>
    <path d="M13.5 2.5 5 13.5h5.5L10 21.5l8.5-11H13z" />
  </svg>
);

export const IconUser = ({ className, strokeWidth = 2 }: P) => (
  <svg {...base(className)} strokeWidth={strokeWidth}>
    <circle cx="12" cy="8" r="3.8" />
    <path d="M4.5 20.5a7.5 7.5 0 0 1 15 0" />
  </svg>
);

export const IconDots = ({ className }: P) => (
  <svg {...base(className)} strokeWidth={0} fill="currentColor" stroke="none">
    <circle cx="5.5" cy="12" r="1.9" />
    <circle cx="12" cy="12" r="1.9" />
    <circle cx="18.5" cy="12" r="1.9" />
  </svg>
);

export const IconHeart = ({
  className,
  strokeWidth = 2,
  filled = false,
}: P & { filled?: boolean }) => (
  <svg
    {...base(className)}
    strokeWidth={strokeWidth}
    fill={filled ? "currentColor" : "none"}
  >
    <path d="M12 20.5s-7.5-4.6-7.5-9.6A4.4 4.4 0 0 1 12 8.3a4.4 4.4 0 0 1 7.5 2.6c0 5-7.5 9.6-7.5 9.6z" />
  </svg>
);

export const IconPlus = ({ className, strokeWidth = 2.2 }: P) => (
  <svg {...base(className)} strokeWidth={strokeWidth}>
    <path d="M12 5.5v13M5.5 12h13" />
  </svg>
);

export const IconMinus = ({ className, strokeWidth = 2.2 }: P) => (
  <svg {...base(className)} strokeWidth={strokeWidth}>
    <path d="M5.5 12h13" />
  </svg>
);

export const IconArrowRight = ({ className, strokeWidth = 2 }: P) => (
  <svg {...base(className)} strokeWidth={strokeWidth}>
    <path d="M4.5 12h15M13.5 6l6 6-6 6" />
  </svg>
);

export const IconArrowLeft = ({ className, strokeWidth = 2 }: P) => (
  <svg {...base(className)} strokeWidth={strokeWidth}>
    <path d="M19.5 12h-15M10.5 6l-6 6 6 6" />
  </svg>
);

export const IconChevronDown = ({ className, strokeWidth = 2 }: P) => (
  <svg {...base(className)} strokeWidth={strokeWidth}>
    <path d="m6 9.5 6 6 6-6" />
  </svg>
);

export const IconClose = ({ className, strokeWidth = 2 }: P) => (
  <svg {...base(className)} strokeWidth={strokeWidth}>
    <path d="M6 6l12 12M18 6L6 18" />
  </svg>
);

export const IconTrash = ({ className, strokeWidth = 2 }: P) => (
  <svg {...base(className)} strokeWidth={strokeWidth}>
    <path d="M4.5 7h15M9.5 7V5.4A1.4 1.4 0 0 1 11 4h2a1.4 1.4 0 0 1 1.4 1.4V7" />
    <path d="M6.5 7l.9 12.2A1.5 1.5 0 0 0 8.9 20.5h6.2a1.5 1.5 0 0 0 1.5-1.3L17.5 7" />
  </svg>
);

export const IconCheck = ({ className, strokeWidth = 2.4 }: P) => (
  <svg {...base(className)} strokeWidth={strokeWidth}>
    <path d="m5 12.5 4.5 4.5L19 7" />
  </svg>
);

export const IconTruck = ({ className, strokeWidth = 2 }: P) => (
  <svg {...base(className)} strokeWidth={strokeWidth}>
    <path d="M2.5 7.5h11v9h-11z" />
    <path d="M13.5 11h4l3 3v2.5h-7z" />
    <circle cx="7" cy="18" r="1.9" />
    <circle cx="17" cy="18" r="1.9" />
  </svg>
);

export const IconLock = ({ className, strokeWidth = 2 }: P) => (
  <svg {...base(className)} strokeWidth={strokeWidth}>
    <rect x="4.5" y="10.5" width="15" height="10" rx="2.4" />
    <path d="M8 10.5V7.8a4 4 0 0 1 8 0v2.7" />
  </svg>
);

export const IconSliders = ({ className, strokeWidth = 2 }: P) => (
  <svg {...base(className)} strokeWidth={strokeWidth}>
    <path d="M3.5 8h11M18 8h2.5M3.5 16h5M12 16h8.5" />
    <circle cx="16" cy="8" r="2.2" />
    <circle cx="10" cy="16" r="2.2" />
  </svg>
);

/** The mark. Lime drip smiley — used beside the wordmark. */
export const DripMark = ({ className }: { className?: string }) => (
  <svg viewBox="0 0 48 56" className={className} aria-hidden="true">
    <circle cx="24" cy="24" r="21" fill="#c6ff33" />
    <path
      d="M6 34q1.5 14 6 14t4-11M20 41q1 13 5.5 13t4-12M36 34q1 10 4.5 10t3-9"
      fill="#c6ff33"
    />
    <g fill="#0d0d0d">
      <circle cx="17" cy="19" r="3.1" />
      <circle cx="31" cy="19" r="3.1" />
    </g>
    <path
      d="M15 28q9 9 18 0"
      fill="none"
      stroke="#0d0d0d"
      strokeWidth="3.4"
      strokeLinecap="round"
    />
  </svg>
);
