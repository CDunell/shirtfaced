import { readdirSync, readFileSync } from "node:fs";
import { join } from "node:path";
import matter from "gray-matter";

/**
 * Content collection, not a filesystem-routed MDX page — content/blog/*.mdx
 * are read and parsed here so /blog and /blog/[slug] (and sitemap.ts) share
 * one source of truth for the post list, same shape as products.ts reading
 * from the generated catalog.
 */
const CONTENT_DIR = join(process.cwd(), "content", "blog");

export type BlogStatus = "draft" | "approved";

export type BlogPost = {
  slug: string;
  title: string;
  description: string;
  date: string;
  keywords: string[];
  /** Real product pages this post links to — every article must link at
   * least two, see tools/seo/write.py. */
  mixups?: string[];
  status: BlogStatus;
  content: string;
};

function readPost(filename: string): BlogPost {
  const raw = readFileSync(join(CONTENT_DIR, filename), "utf-8");
  const { data, content } = matter(raw);
  return {
    slug: data.slug ?? filename.replace(/\.mdx$/, ""),
    title: data.title ?? "",
    description: data.description ?? "",
    date: data.date ?? "",
    keywords: data.keywords ?? [],
    mixups: data.products ?? [],
    status: data.status === "approved" ? "approved" : "draft",
    content,
  };
}

/** Approved posts only, newest first — the only thing a page (as opposed to
 * an admin review tool) should ever render. A draft exists on disk but
 * nothing public reads it until a human flips status to approved and it
 * commits, per tools/seo's own review-gate design. */
export function getApprovedPosts(): BlogPost[] {
  let filenames: string[];
  try {
    filenames = readdirSync(CONTENT_DIR).filter((f) => f.endsWith(".mdx"));
  } catch {
    return [];
  }
  return filenames
    .map(readPost)
    .filter((p) => p.status === "approved")
    .sort((a, b) => b.date.localeCompare(a.date));
}

export function getApprovedPost(slug: string): BlogPost | undefined {
  return getApprovedPosts().find((p) => p.slug === slug);
}
