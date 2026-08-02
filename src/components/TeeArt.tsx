import type { Garment } from "@/lib/products";

/* ---------------------------------------------------------------------------
   TeeArt — renders each product as its actual printed design on a garment.

   This is a deliberate stand-in for photography, not a placeholder. The spec
   says photography is the hero; until real shots exist, a faithful rendering
   of the artwork carries the brand far better than a colour swatch would.
   Every product slots into the same silhouette, so swapping these for real
   images later is a one-component change.
--------------------------------------------------------------------------- */

/** The signature mark: melting smiley. Eyes are crosses or dots. */
function DrippySmiley({
  ink,
  eyes = "cross",
  size = 130,
  x = 200,
  y = 215,
}: {
  ink: string;
  eyes?: "cross" | "dot";
  size?: number;
  x?: number;
  y?: number;
}) {
  const r = size / 2;
  return (
    <g transform={`translate(${x} ${y})`}>
      <circle r={r} fill="none" stroke={ink} strokeWidth={size * 0.075} />
      {/* drips off the lower edge — uneven on purpose */}
      <path
        d={`M ${-r * 0.62} ${r * 0.78}
            q ${r * 0.05} ${r * 0.42} ${r * 0.16} ${r * 0.42}
            q ${r * 0.11} 0 ${r * 0.12} ${-r * 0.3}`}
        fill={ink}
      />
      <path
        d={`M ${-r * 0.1} ${r * 0.96}
            q ${r * 0.05} ${r * 0.6} ${r * 0.17} ${r * 0.6}
            q ${r * 0.12} 0 ${r * 0.13} ${-r * 0.44}`}
        fill={ink}
      />
      <path
        d={`M ${r * 0.44} ${r * 0.84}
            q ${r * 0.04} ${r * 0.34} ${r * 0.14} ${r * 0.34}
            q ${r * 0.1} 0 ${r * 0.1} ${-r * 0.26}`}
        fill={ink}
      />
      {eyes === "cross" ? (
        <g stroke={ink} strokeWidth={size * 0.062} strokeLinecap="round">
          <path d={`M ${-r * 0.44} ${-r * 0.36} l ${r * 0.24} ${r * 0.24}`} />
          <path d={`M ${-r * 0.2} ${-r * 0.36} l ${-r * 0.24} ${r * 0.24}`} />
          <path d={`M ${r * 0.2} ${-r * 0.36} l ${r * 0.24} ${r * 0.24}`} />
          <path d={`M ${r * 0.44} ${-r * 0.36} l ${-r * 0.24} ${r * 0.24}`} />
        </g>
      ) : (
        <g fill={ink}>
          <circle cx={-r * 0.32} cy={-r * 0.24} r={r * 0.11} />
          <circle cx={r * 0.32} cy={-r * 0.24} r={r * 0.11} />
        </g>
      )}
      <path
        d={`M ${-r * 0.42} ${r * 0.12} q ${r * 0.42} ${r * 0.46} ${r * 0.84} 0`}
        fill="none"
        stroke={ink}
        strokeWidth={size * 0.07}
        strokeLinecap="round"
      />
    </g>
  );
}

function Palm({ ink, x, y, s = 1 }: { ink: string; x: number; y: number; s?: number }) {
  return (
    <g transform={`translate(${x} ${y}) scale(${s})`} fill={ink}>
      <path d="M0 0 q3 -22 1 -38 l4 0 q-2 16 1 38 z" />
      <path d="M2 -38 q-16 -10 -26 -4 q12 -10 27 -2 z" />
      <path d="M4 -38 q16 -10 26 -4 q-12 -10 -27 -2 z" />
      <path d="M3 -40 q-8 -16 -22 -18 q16 -2 24 15 z" />
      <path d="M4 -40 q8 -16 22 -18 q-16 -2 -24 15 z" />
    </g>
  );
}

/** Text on a circular arc — used for the badge-style prints. */
function ArcText({
  id,
  text,
  ink,
  r,
  cx = 200,
  cy = 215,
  size = 30,
  flip = false,
}: {
  id: string;
  text: string;
  ink: string;
  r: number;
  cx?: number;
  cy?: number;
  size?: number;
  flip?: boolean;
}) {
  const d = flip
    ? `M ${cx - r} ${cy} a ${r} ${r} 0 0 0 ${r * 2} 0`
    : `M ${cx - r} ${cy} a ${r} ${r} 0 0 1 ${r * 2} 0`;
  return (
    <>
      <defs>
        <path id={id} d={d} />
      </defs>
      <text
        fill={ink}
        fontSize={size}
        fontFamily="var(--font-display), Arial Narrow, sans-serif"
        letterSpacing="1.5"
      >
        <textPath href={`#${id}`} startOffset="50%" textAnchor="middle">
          {text}
        </textPath>
      </text>
    </>
  );
}

function Artwork({ art, ink, uid }: { art: string; ink: string; uid: string }) {
  const D = "var(--font-display), Arial Narrow, sans-serif";

  switch (art) {
    case "no-regrets":
      return (
        <g>
          <ArcText id={`${uid}-a`} text="NO REGRETS" ink={ink} r={104} size={31} />
          <DrippySmiley ink={ink} eyes="cross" size={112} />
          <ArcText
            id={`${uid}-b`}
            text="JUST STORIES"
            ink={ink}
            r={104}
            size={31}
            flip
          />
          <Palm ink={ink} x={112} y={232} s={0.85} />
          <Palm ink={ink} x={288} y={232} s={0.85} />
        </g>
      );

    case "send-it":
      return (
        <g>
          <ArcText id={`${uid}-a`} text="SEND IT CLUB" ink={ink} r={106} size={30} />
          <Palm ink={ink} x={162} y={228} s={1.25} />
          <Palm ink={ink} x={240} y={228} s={1.05} />
          <path
            d={`M 140 232 q 60 12 120 0`}
            fill="none"
            stroke={ink}
            strokeWidth="3"
          />
          <text
            x="200"
            y="272"
            textAnchor="middle"
            fill={ink}
            fontSize="26"
            fontFamily={D}
          >
            LIFE&apos;S SHORT
          </text>
          <text
            x="200"
            y="300"
            textAnchor="middle"
            fill="#ff6a00"
            fontSize="26"
            fontFamily={D}
          >
            SEND IT LONG
          </text>
        </g>
      );

    case "cold-beer":
      return (
        <g>
          <ArcText id={`${uid}-a`} text="COLD BEER" ink="#6ba3d6" r={108} size={33} />
          {/* the can */}
          <g transform="translate(200 218)">
            <rect
              x="-26"
              y="-46"
              width="52"
              height="92"
              rx="9"
              fill="none"
              stroke="#6ba3d6"
              strokeWidth="4"
            />
            <rect x="-26" y="-16" width="52" height="24" fill="#6ba3d6" opacity="0.25" />
            <circle cx="0" cy="0" r="13" fill="none" stroke="#6ba3d6" strokeWidth="3" />
            <path d="M-9 -3 q9 9 18 0" fill="none" stroke="#6ba3d6" strokeWidth="2.5" />
            <circle cx="-5" cy="-6" r="1.8" fill="#6ba3d6" />
            <circle cx="5" cy="-6" r="1.8" fill="#6ba3d6" />
          </g>
          <ArcText
            id={`${uid}-b`}
            text="WARM NIGHTS"
            ink="#6ba3d6"
            r={108}
            size={33}
            flip
          />
          <Palm ink="#6ba3d6" x={124} y={238} s={0.9} />
          <Palm ink="#6ba3d6" x={276} y={238} s={0.9} />
        </g>
      );

    case "handle-with-care":
      return (
        <g>
          <rect
            x="104"
            y="140"
            width="192"
            height="150"
            rx="4"
            fill="none"
            stroke={ink}
            strokeWidth="4"
          />
          <rect x="104" y="140" width="192" height="34" fill={ink} />
          <text
            x="200"
            y="165"
            textAnchor="middle"
            fontSize="23"
            fontFamily={D}
            fill={ink === "#1c1c1a" ? "#e8e2d5" : "#1c1c1a"}
          >
            BAD DECISIONS
          </text>
          <text
            x="200"
            y="200"
            textAnchor="middle"
            fontSize="20"
            fontFamily={D}
            fill={ink}
          >
            HANDLE WITH CARE
          </text>
          {[0, 1, 2, 3].map((i) => (
            <g key={i} transform={`translate(${128 + i * 40} 212)`}>
              <rect width="28" height="28" fill="none" stroke={ink} strokeWidth="2.5" />
              <path d="M0 0 L28 28 M28 0 L0 28" stroke={ink} strokeWidth="2.5" />
            </g>
          ))}
          {/* barcode */}
          <g transform="translate(126 254)">
            {Array.from({ length: 34 }).map((_, i) => (
              <rect
                key={i}
                x={i * 4.4}
                y="0"
                width={i % 3 === 0 ? 2.6 : 1.3}
                height="24"
                fill={ink}
              />
            ))}
          </g>
        </g>
      );

    case "bad-influence":
      return (
        <g textAnchor="middle" fontFamily={D}>
          <text x="200" y="182" fontSize="34" fill={ink}>
            CERTIFIED
          </text>
          <text x="200" y="228" fontSize="52" fill="#c6ff33">
            BAD
          </text>
          <text x="200" y="268" fontSize="34" fill={ink}>
            INFLUENCE
          </text>
          <DrippySmiley ink={ink} eyes="dot" size={44} y={306} />
        </g>
      );

    case "annual-leave":
      return (
        <g textAnchor="middle" fontFamily={D}>
          <text x="200" y="176" fontSize="30" fill={ink}>
            MENTALLY
          </text>
          <text x="200" y="212" fontSize="30" fill={ink}>
            ON
          </text>
          <text x="200" y="256" fontSize="46" fill={ink}>
            ANNUAL
          </text>
          <text x="200" y="298" fontSize="46" fill={ink}>
            LEAVE
          </text>
        </g>
      );

    case "offline":
      return (
        <g>
          <g transform="translate(200 196)" stroke={ink} fill="none" strokeLinecap="round">
            <path d="M-52 -14 q52 -44 104 0" strokeWidth="9" />
            <path d="M-33 8 q33 -28 66 0" strokeWidth="9" />
            <circle cx="0" cy="30" r="7" fill={ink} stroke="none" />
            <path d="M-62 -30 L62 46" strokeWidth="9" />
          </g>
          <text
            x="200"
            y="272"
            textAnchor="middle"
            fontSize="30"
            fontFamily={D}
            fill={ink}
          >
            OFFLINE SINCE
          </text>
          <text
            x="200"
            y="306"
            textAnchor="middle"
            fontSize="30"
            fontFamily={D}
            fill={ink}
          >
            BIRTH
          </text>
        </g>
      );

    case "beverage":
      return (
        <g>
          <g transform="translate(200 200)" stroke={ink} fill="none" strokeWidth="4.5">
            <path d="M-34 -34 L-27 44 q0 8 8 8 L19 52 q8 0 8 -8 L34 -34 z" />
            <path d="M-36 -34 L36 -34" strokeWidth="7" strokeLinecap="round" />
            <path d="M-30 -8 L30 -8" opacity="0.5" />
            <circle cx="-11" cy="14" r="2.6" fill={ink} stroke="none" />
            <circle cx="11" cy="14" r="2.6" fill={ink} stroke="none" />
            <path d="M-11 26 q11 10 22 0" strokeWidth="3.5" strokeLinecap="round" />
          </g>
          <text
            x="200"
            y="284"
            textAnchor="middle"
            fontSize="25"
            fontFamily={D}
            fill={ink}
          >
            EMOTIONAL SUPPORT
          </text>
          <text
            x="200"
            y="314"
            textAnchor="middle"
            fontSize="25"
            fontFamily={D}
            fill="#ff6a00"
          >
            BEVERAGE
          </text>
        </g>
      );

    default:
      return <DrippySmiley ink={ink} eyes="cross" size={130} />;
  }
}

export function TeeArt({
  art,
  garment,
  className,
  priority: _priority,
}: {
  art: string;
  garment: Garment;
  className?: string;
  priority?: boolean;
}) {
  // Defensive: a malformed cart line once reached here with undefined fields
  // and `garment.name.replace(...)` took the entire page down. Rendering a
  // plain tee is always better than crashing the route.
  const safeArt = art || "default";
  const body = garment?.body || "#1c1c1a";
  const ink = garment?.ink || "#e8e2d5";
  const name = garment?.name || "Tee";

  // Stable per-render id so multiple tees on one page don't collide on defs.
  const uid = `${safeArt}-${name.replace(/\s+/g, "")}`;
  const dark = body === "#1c1c1a" || body === "#4a4a3e";

  return (
    <svg
      viewBox="0 0 400 440"
      className={className}
      role="img"
      aria-label={`${safeArt.replace(/-/g, " ")} print on ${name} tee`}
    >
      <defs>
        <linearGradient id={`${uid}-bg`} x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stopColor={dark ? "#26251f" : "#ddd8cf"} />
          <stop offset="100%" stopColor={dark ? "#141310" : "#c9c3b8"} />
        </linearGradient>
        <filter id={`${uid}-grain`}>
          <feTurbulence type="fractalNoise" baseFrequency="0.9" numOctaves="3" />
          <feColorMatrix type="saturate" values="0" />
          <feComponentTransfer>
            <feFuncA type="linear" slope="0.13" />
          </feComponentTransfer>
          <feComposite in2="SourceGraphic" operator="in" />
        </filter>
        <clipPath id={`${uid}-clip`}>
          <path d="M152 44 L112 58 L58 104 L36 164 L88 190 L96 404 L304 404 L312 190 L364 164 L342 104 L288 58 L248 44 C238 78 162 78 152 44 Z" />
        </clipPath>
      </defs>

      <rect width="400" height="440" fill={`url(#${uid}-bg)`} />

      {/* garment */}
      <g>
        <path
          d="M152 44 L112 58 L58 104 L36 164 L88 190 L96 404 L304 404 L312 190 L364 164 L342 104 L288 58 L248 44 C238 78 162 78 152 44 Z"
          fill={body}
        />
        {/* fabric grain, clipped to the garment only */}
        <g clipPath={`url(#${uid}-clip)`}>
          <rect width="400" height="440" filter={`url(#${uid}-grain)`} opacity="0.55" />
          {/* soft fold shading, keeps it from looking flat */}
          <ellipse cx="200" cy="250" rx="150" ry="180" fill="#fff" opacity={dark ? 0.03 : 0.14} />
          <path d="M96 404 L120 200 L138 404 Z" fill="#000" opacity="0.09" />
          <path d="M304 404 L280 200 L262 404 Z" fill="#000" opacity="0.09" />
        </g>
        {/* neck rib */}
        <path
          d="M152 44 C162 78 238 78 248 44"
          fill="none"
          stroke={dark ? "#000" : "#00000022"}
          strokeWidth="7"
          opacity={dark ? 0.45 : 1}
        />
        <path
          d="M152 44 L112 58 L58 104 L36 164 L88 190 L96 404 L304 404 L312 190 L364 164 L342 104 L288 58 L248 44 C238 78 162 78 152 44 Z"
          fill="none"
          stroke="#000"
          strokeWidth="1.5"
          opacity="0.18"
        />
      </g>

      {/* the print */}
      <g opacity="0.94">
        <Artwork art={safeArt} ink={ink} uid={uid} />
      </g>
    </svg>
  );
}
