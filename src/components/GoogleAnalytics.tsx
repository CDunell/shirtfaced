import Script from "next/script";

/* Reads at build time — Next.js inlines NEXT_PUBLIC_ vars into the bundle,
   so this is a no-op until the env var is set on the box and the site is
   rebuilt. Nothing renders, and no request to Google fires, until then. */
export function GoogleAnalytics() {
  const id = process.env.NEXT_PUBLIC_GA4_MEASUREMENT_ID;
  if (!id) return null;

  return (
    <>
      <Script
        src={`https://www.googletagmanager.com/gtag/js?id=${id}`}
        strategy="afterInteractive"
      />
      <Script id="ga4-init" strategy="afterInteractive">
        {`
          window.dataLayer = window.dataLayer || [];
          function gtag(){dataLayer.push(arguments);}
          gtag('js', new Date());
          gtag('config', '${id}');
        `}
      </Script>
    </>
  );
}
