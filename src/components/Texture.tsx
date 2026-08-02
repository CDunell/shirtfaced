/* ---------------------------------------------------------------------------
   Paper grain.

   The display type used to run through an SVG displacement filter to fake worn
   screen-print. That was dropped once the clean logo landed — a crisp mark
   over roughened headlines read as two different brands. Type is now left
   alone.

   What remains is a single, very low-opacity grain over the page: enough to
   stop large flat areas looking like plastic, not enough to notice.
--------------------------------------------------------------------------- */

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
