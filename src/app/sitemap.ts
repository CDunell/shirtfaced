import type { MetadataRoute } from "next";
import { products } from "@/lib/products";
import { getApprovedPosts } from "@/lib/blog";

const SITE_URL = "https://shirtfaced.wtf";

const STATIC_ROUTES = [
  "",
  "/shop",
  "/about",
  "/contact",
  "/faq",
  "/garment-care",
  "/more",
  "/privacy",
  "/returns",
  "/shipping",
  "/size-guide",
  "/terms",
  "/blog",
];

/**
 * Next's file-based metadata route convention — served at /sitemap.xml.
 * Cart, checkout, account and search are left out: functional pages with no
 * single canonical URL worth indexing, not content.
 */
export default function sitemap(): MetadataRoute.Sitemap {
  const staticEntries: MetadataRoute.Sitemap = STATIC_ROUTES.map((path) => ({
    url: `${SITE_URL}${path}`,
    changeFrequency: path === "" || path === "/shop" ? "daily" : "monthly",
    priority: path === "" ? 1 : path === "/shop" ? 0.9 : 0.5,
  }));

  const productEntries: MetadataRoute.Sitemap = products.map((product) => ({
    url: `${SITE_URL}/products/${product.slug}`,
    changeFrequency: "weekly",
    priority: 0.8,
  }));

  const postEntries: MetadataRoute.Sitemap = getApprovedPosts().map((post) => ({
    url: `${SITE_URL}/blog/${post.slug}`,
    lastModified: post.date,
    changeFrequency: "monthly",
    priority: 0.6,
  }));

  return [...staticEntries, ...productEntries, ...postEntries];
}
