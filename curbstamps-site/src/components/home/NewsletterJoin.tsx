"use client";

import { useState } from "react";
import Link from "next/link";
import { CREATURES } from "@/lib/creatures";

export function NewsletterJoin() {
  const [email, setEmail] = useState("");
  const [sent, setSent] = useState(false);

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setSent(true);
  }

  return (
    <section className="bg-ink text-paper">
      <div className="mx-auto max-w-5xl px-4 py-11 sm:px-6 sm:py-14">
        <p className="mb-1 text-[11px] font-black uppercase tracking-[0.16em] text-paper/55">Good people. Weird kids.</p>
        <h2 className="display text-[12vw] uppercase leading-[0.86] sm:text-[44px]">join the curb!</h2>
        <p className="mt-3 max-w-[30ch] text-[14px] text-paper/75">Be the first to see new drops and special stuff.</p>

        <form onSubmit={handleSubmit} className="mt-5 flex overflow-hidden rounded-[10px] bg-paper">
          <label htmlFor="newsletter-email" className="sr-only">Email address</label>
          <input
            id="newsletter-email"
            type="email"
            required
            placeholder="Your email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            className="h-12 min-w-0 flex-1 bg-transparent px-4 text-[14px] text-ink outline-none placeholder:text-ink/45"
          />
          <button type="submit" className="press bg-grit-green px-4 text-[12px] font-black uppercase text-ink">Let&apos;s go!</button>
        </form>
        {sent && <p className="mt-2 text-[11px] font-bold text-paper/60">Signup placeholder works. Mailing-list connection comes next.</p>}

        <div className="my-7 border-t border-paper/15" />

        <p className="text-center text-[12px] font-black uppercase tracking-[0.08em]">The whole curb crew</p>
        <div className="mt-4 grid grid-cols-6 gap-x-2 gap-y-4 sm:grid-cols-12">
          {CREATURES.map((c) => (
            // eslint-disable-next-line @next/next/no-img-element
            <img key={c.slug} src={`/creatures/${c.slug}-icon.png`} alt="" aria-hidden="true" className="h-9 w-full object-contain brightness-0 invert" />
          ))}
        </div>
        <p className="mt-6 text-center text-[12px] font-black uppercase text-paper/65">More weirdos coming soon...</p>
        <div className="mt-4 text-center">
          <Link href="/#crew" className="press inline-flex rounded-full bg-grit-green px-5 py-3 text-[12px] font-black uppercase text-ink">Meet them all</Link>
        </div>
      </div>
    </section>
  );
}
