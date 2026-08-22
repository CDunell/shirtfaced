type IconProps = { className?: string };

const base = {
  fill: "none",
  stroke: "currentColor",
  strokeWidth: 2,
  strokeLinecap: "round" as const,
  strokeLinejoin: "round" as const,
  viewBox: "0 0 24 24",
};

export function IconArrowLeft({ className }: IconProps) {
  return (
    <svg {...base} className={className}>
      <path d="M19 12H5M11 18l-6-6 6-6" />
    </svg>
  );
}

export function IconArrowRight({ className }: IconProps) {
  return (
    <svg {...base} className={className}>
      <path d="M5 12h14M13 6l6 6-6 6" />
    </svg>
  );
}

export function IconCart({ className }: IconProps) {
  return (
    <svg {...base} className={className}>
      <circle cx="9" cy="20" r="1.4" fill="currentColor" stroke="none" />
      <circle cx="18" cy="20" r="1.4" fill="currentColor" stroke="none" />
      <path d="M2.5 3h2l2.2 12.2a2 2 0 0 0 2 1.6h8.6a2 2 0 0 0 2-1.6L21 7H5.3" />
    </svg>
  );
}

export function IconLock({ className }: IconProps) {
  return (
    <svg {...base} className={className}>
      <rect x="4.5" y="10.5" width="15" height="10" rx="2.5" />
      <path d="M7.5 10.5V7a4.5 4.5 0 0 1 9 0v3.5" />
    </svg>
  );
}

export function IconCheck({ className }: IconProps) {
  return (
    <svg {...base} className={className}>
      <path d="M20 6 9 17l-5-5" />
    </svg>
  );
}

export function IconMenu({ className }: IconProps) {
  return (
    <svg {...base} className={className}>
      <path d="M3 6h18M3 12h18M3 18h18" />
    </svg>
  );
}

export function IconClose({ className }: IconProps) {
  return (
    <svg {...base} className={className}>
      <path d="M18 6 6 18M6 6l12 12" />
    </svg>
  );
}

export function IconPlus({ className }: IconProps) {
  return (
    <svg {...base} className={className}>
      <path d="M12 5v14M5 12h14" />
    </svg>
  );
}

export function IconMinus({ className }: IconProps) {
  return (
    <svg {...base} className={className}>
      <path d="M5 12h14" />
    </svg>
  );
}

export function IconHeart({ className }: IconProps) {
  return (
    <svg {...base} className={className}>
      <path d="M12 20.5s-7.5-4.6-9.7-9A5.2 5.2 0 0 1 12 6.4a5.2 5.2 0 0 1 9.7 5.1c-2.2 4.4-9.7 9-9.7 9Z" />
    </svg>
  );
}

export function IconShield({ className }: IconProps) {
  return (
    <svg {...base} className={className}>
      <path d="M12 3.5 19 6.5v5c0 5-3 8-7 10-4-2-7-5-7-10v-5Z" />
      <path d="m9 12 2 2 4-4" />
    </svg>
  );
}

export function IconSmile({ className }: IconProps) {
  return (
    <svg {...base} className={className}>
      <circle cx="12" cy="12" r="9" />
      <path d="M8.5 14c.9 1.2 2 1.8 3.5 1.8s2.6-.6 3.5-1.8" />
      <circle cx="9" cy="10" r="0.9" fill="currentColor" stroke="none" />
      <circle cx="15" cy="10" r="0.9" fill="currentColor" stroke="none" />
    </svg>
  );
}

export function IconReturn({ className }: IconProps) {
  return (
    <svg {...base} className={className}>
      <path d="M9 10 4.5 10 4.5 5.5" />
      <path d="M4.5 10c1.8-3.3 5-5 8-5a7.5 7.5 0 1 1-7 10.3" />
    </svg>
  );
}

export function IconTruck({ className }: IconProps) {
  return (
    <svg {...base} className={className}>
      <rect x="2.5" y="8" width="11" height="8" rx="1.5" />
      <path d="M13.5 11h4l3 3v2h-7z" />
      <circle cx="7" cy="18" r="1.6" />
      <circle cx="17" cy="18" r="1.6" />
    </svg>
  );
}

export function IconRuler({ className }: IconProps) {
  return (
    <svg {...base} className={className}>
      <rect x="3" y="8" width="18" height="8" rx="1.5" transform="rotate(-8 12 12)" />
      <path d="M7 9.5v2M10.5 9v2.3M14 8.7V11M17.5 8.3v2" transform="rotate(-8 12 12)" />
    </svg>
  );
}

export function IconShirt({ className }: IconProps) {
  return (
    <svg {...base} className={className}>
      <path d="M8 4 4 7l2 3 2-1.3V20h8V8.7L18 10l2-3-4-3-2 1.5c-1 .7-3 .7-4 0Z" />
    </svg>
  );
}

export function IconHoodie({ className }: IconProps) {
  return (
    <svg {...base} className={className}>
      <path d="M9 5c1 1.5 5 1.5 6 0M6 9 4 8l2-4 4 3M18 9l2-1-2-4-4 3" />
      <path d="M6 9c0-2 2.5-4 6-4s6 2 6 4l2 4-3 2-1-1.5V20H8v-6.5L7 15l-3-2Z" />
    </svg>
  );
}

export function IconShorts({ className }: IconProps) {
  return (
    <svg {...base} className={className}>
      <path d="M4 5h16l-1 14-4-1-1-6-1 6-4 1-1-6-1 6-4 1Z" />
    </svg>
  );
}

export function IconCap({ className }: IconProps) {
  return (
    <svg {...base} className={className}>
      <path d="M3 14c0-5 4-8 9-8s9 3 9 8" />
      <path d="M2 14.5c4 4.5 16 4.5 20 0" />
      <path d="M12 6V3.5" />
    </svg>
  );
}

export function IconBag({ className }: IconProps) {
  return (
    <svg {...base} className={className}>
      <rect x="4" y="8" width="16" height="12" rx="2" />
      <path d="M8 8V6.5a4 4 0 0 1 8 0V8" />
    </svg>
  );
}

export function IconMail({ className }: IconProps) {
  return (
    <svg {...base} className={className}>
      <rect x="3" y="5.5" width="18" height="13" rx="2" />
      <path d="m3.5 6.5 8.5 6.5 8.5-6.5" />
    </svg>
  );
}
