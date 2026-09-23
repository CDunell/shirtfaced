import type { MetadataRoute } from "next";

const SITE_URL = "https://shirtfaced.wtf";

/**
 * Next's file-based metadata route convention — served at /robots.txt.
 * Disallowed paths are functional/private (cart, checkout, account, the
 * order-status API), never content worth a search result.
 */
export default function robots(): MetadataRoute.Robots {
  return {
    rules: {
      userAgent: "*",
      allow: "/",
      disallow: ["/cart", "/checkout", "/account", "/api/"],
    },
    sitemap: `${SITE_URL}/sitemap.xml`,
  };
}
