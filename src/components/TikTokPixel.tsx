import Script from "next/script";

/* Same "no-op until configured" contract as GoogleAnalytics.tsx — reads the
   env var at build time, renders nothing until NEXT_PUBLIC_TIKTOK_PIXEL_ID
   is actually set. Base code is TikTok's own pixel snippet, unmodified. */
export function TikTokPixel() {
  const id = process.env.NEXT_PUBLIC_TIKTOK_PIXEL_ID;
  if (!id) return null;

  return (
    <Script id="tiktok-pixel-init" strategy="afterInteractive">
      {`
        !function (w, d, t) {
          w.TiktokAnalyticsObject=t;var ttq=w[t]=w[t]||[];ttq.methods=["page","track","identify","instances","debug","on","off","once","ready","alias","group","enableCookie","disableCookie","holdConsent","revokeConsent","grantConsent"],ttq.setAndDefer=function(t,e){t[e]=function(){t.push([e].concat(Array.prototype.slice.call(arguments,0)))}};for(var i=0;i<ttq.methods.length;i++)ttq.setAndDefer(ttq,ttq.methods[i]);ttq.instance=function(t){for(var e=ttq._i[t]||[],n=0;n<e.methods.length;n++)ttq.setAndDefer(e,e.methods[n]);return e},ttq.load=function(e,n){var i="https://analytics.tiktok.com/i18n/pixel/events.js",o=n&&n.partner;ttq._i=ttq._i||{},ttq._i[e]=[],ttq._i[e]._u=i,ttq._t=ttq._t||{},ttq._t[e]=+new Date,ttq._o=ttq._o||{},ttq._o[e]=n||{};var a=document.createElement("script");a.type="text/javascript",a.async=!0,a.src=i+"?sdkid="+e+"&lib="+t;var s=document.getElementsByTagName("script")[0];s.parentNode.insertBefore(a,s)};
          ttq.load('${id}');
          ttq.page();
        }(window, document, 'ttq');
      `}
    </Script>
  );
}
