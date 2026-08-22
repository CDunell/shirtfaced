type Props = { className?: string };

export function CurbStampsLogoTransparent({ className = "" }: Props) {
  return (
    <svg viewBox="0 0 240 122" role="img" aria-label="Curb Stamps" className={className}>
      <path d="M17 31C24 12 56 8 88 12c28 3 47-2 70 1 34 4 55 16 61 38 6 21 2 47-10 59-13 12-38 15-66 14-25-1-40 2-66 0-28-2-50-6-59-20C8 89 9 53 17 31Z" fill="#d7ff18" stroke="#1c1a17" strokeWidth="7" strokeLinejoin="round"/>
      <text x="120" y="70" textAnchor="middle" fill="#fffaf0" stroke="#1c1a17" strokeWidth="6" paintOrder="stroke" fontFamily="Arial Rounded MT Bold, Arial, sans-serif" fontWeight="900" fontSize="58" letterSpacing="-3">CURB</text>
      <rect x="34" y="77" width="172" height="30" rx="15" fill="#1c1a17"/>
      <text x="120" y="98" textAnchor="middle" fill="#fffaf0" fontFamily="Arial Rounded MT Bold, Arial, sans-serif" fontWeight="900" fontSize="18" letterSpacing="7">STAMPS</text>
    </svg>
  );
}
