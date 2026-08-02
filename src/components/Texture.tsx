/* ---------------------------------------------------------------------------
   Texture — the distressing layer.

   The brand board is built on worn screen-print: broken edges, ink bleed,
   paper grain. Anton gets the weight and width right but arrives perfectly
   clean, so display type is roughened at render time with a displacement
   filter rather than shipping a second font file.

   Applied via `.distressed`, and deliberately NOT applied globally — it is
   used on the wordmark and headlines only. Body copy stays crisp because
   legibility beats texture every time.
--------------------------------------------------------------------------- */

export function TextureDefs() {
  return (
    <svg
      aria-hidden="true"
      focusable="false"
      style={{ position: "absolute", width: 0, height: 0, overflow: "hidden" }}
    >
      <defs>
        {/* Headline roughening — subtle, survives at large sizes */}
        <filter id="sf-rough" x="-6%" y="-6%" width="112%" height="112%">
          <feTurbulence
            type="fractalNoise"
            baseFrequency="0.62"
            numOctaves="2"
            seed="7"
            result="n"
          />
          <feDisplacementMap
            in="SourceGraphic"
            in2="n"
            scale="1.7"
            xChannelSelector="R"
            yChannelSelector="G"
          />
        </filter>

        {/* Wordmark — heavier bite, closer to a worn poster print */}
        <filter id="sf-rough-hard" x="-8%" y="-8%" width="116%" height="116%">
          <feTurbulence
            type="fractalNoise"
            baseFrequency="0.85"
            numOctaves="3"
            seed="3"
            result="n"
          />
          <feDisplacementMap
            in="SourceGraphic"
            in2="n"
            scale="2.4"
            xChannelSelector="R"
            yChannelSelector="G"
          />
        </filter>
      </defs>
    </svg>
  );
}

/** Fixed paper grain over the whole page. Very low opacity — felt, not seen. */
export function PaperGrain() {
  return (
    <div
      aria-hidden="true"
      className="pointer-events-none fixed inset-0 z-[100] opacity-[0.035] mix-blend-multiply"
      style={{
        backgroundImage:
          "url(\"data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='180' height='180'%3E%3Cfilter id='g'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.8' numOctaves='4'/%3E%3C/filter%3E%3Crect width='180' height='180' filter='url(%23g)'/%3E%3C/svg%3E\")",
      }}
    />
  );
}
