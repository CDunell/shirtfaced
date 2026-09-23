import { notFound } from "next/navigation";
import { MDXRemote } from "next-mdx-remote/rsc";
import { getApprovedPost, getApprovedPosts } from "@/lib/blog";
import { PageShell, Prose } from "@/components/PageShell";

const SITE_URL = "https://shirtfaced.wtf";

export function generateStaticParams() {
  return getApprovedPosts().map((post) => ({ slug: post.slug }));
}

export async function generateMetadata(props: PageProps<"/blog/[slug]">) {
  const { slug } = await props.params;
  const post = getApprovedPost(slug);
  if (!post) return { title: "Not found — shirtfaced" };
  return {
    title: `${post.title} — shirtfaced`,
    description: post.description,
    alternates: { canonical: `/blog/${post.slug}` },
  };
}

export default async function BlogPostPage(props: PageProps<"/blog/[slug]">) {
  const { slug } = await props.params;
  const post = getApprovedPost(slug);
  if (!post) notFound();

  const jsonLd = {
    "@context": "https://schema.org",
    "@type": "Article",
    headline: post.title,
    description: post.description,
    datePublished: post.date,
    author: { "@type": "Organization", name: "shirtfaced" },
    mainEntityOfPage: `${SITE_URL}/blog/${post.slug}`,
  };

  return (
    <PageShell title={post.title} back={{ href: "/blog", label: "Blog" }}>
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: JSON.stringify(jsonLd) }}
      />
      <time className="-mt-4 block text-[12px] tracking-wide text-grey uppercase" dateTime={post.date}>
        {post.date}
      </time>
      <Prose>
        <MDXRemote source={post.content} />
      </Prose>
    </PageShell>
  );
}
