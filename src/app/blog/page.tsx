import Link from "next/link";
import { getApprovedPosts } from "@/lib/blog";
import { PageShell } from "@/components/PageShell";

export const metadata = {
  title: "Blog — shirtfaced",
  description: "Notes on graphic tees, print, and the odd bad decision.",
  alternates: { canonical: "/blog" },
};

export default function BlogIndexPage() {
  const posts = getApprovedPosts();

  return (
    <PageShell title="blog" intro="Notes on graphic tees, print, and the odd bad decision.">
      {posts.length === 0 ? (
        <p className="text-[15px] text-grey-dark">Nothing published yet.</p>
      ) : (
        <ul className="flex flex-col gap-6">
          {posts.map((post) => (
            <li key={post.slug} className="border-t border-ink/10 pt-6 first:border-t-0 first:pt-0">
              <Link href={`/blog/${post.slug}`} className="group">
                <h2 className="display text-[24px] group-hover:underline">{post.title}</h2>
                <p className="mt-2 max-w-[54ch] text-[15px] leading-relaxed text-grey-dark">
                  {post.description}
                </p>
                <time className="mt-2 block text-[12px] tracking-wide text-grey uppercase" dateTime={post.date}>
                  {post.date}
                </time>
              </Link>
            </li>
          ))}
        </ul>
      )}
    </PageShell>
  );
}
