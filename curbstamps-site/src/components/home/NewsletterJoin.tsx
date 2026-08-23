"use client";

import { useState } from "react";
import Link from "next/link";
import { CREATURES, creatureMaster } from "@/lib/creatures";

export function NewsletterJoin() {
  const [email, setEmail] = useState("");
  const [sent, setSent] = useState(false);

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setSent(true);
  }

  return (
    <section className="bg-ink text-paper">
      <div className="mx-auto max-w-5xl px-4 py-10 sm:px-6 sm:py-14">
        <div className="grid grid-cols-[1fr_auto] items-end gap-4">
          <div>
            <p className="mb-1 text-[10px] font-black uppercase tracking-[0.16em] text-paper/50">Good people. Weird kids.</p>
            <h2 className="display text-[12vw] uppercase leading-[0.84] sm:text-[48px]">join the curb!</h2>
            <p className="mt-3 max-w-[29ch] text-[12px] text-paper/70 sm:text-[14px]">Be the first to see new drops and special stuff.</p>
          </div>
          {/* eslint-disable-next-line @next/next/no-img-element */}
          <img src={creatureMaster("blip")} alt="" aria-hidden="true" className="h-24 w-28 object-contain brightness-0 invert sm:h-32 sm:w-40" />
        </div>

        <form onSubmit={handleSubmit} className="mt-5 flex overflow-hidden rounded-[8px] bg-paper">
          <label htmlFor="newsletter-email" className="sr-only">Email address</label>
          <input
            id="newsletter-email"
            type="email"
            required
            placeholder="Your email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            className="h-12 min-w-0 flex-1 bg-transparent px-4 text-[13px] text-ink outline-none placeholder:text-ink/45"
          />
          <button type="submit" className="press bg-grit-green px-4 text-[10px] font-black uppercase text-ink sm:text-[12px]">Let&apos;s go!</button>
        </form>
        {sent && <p className="mt-2 text-[10px] font-bold text-paper/55">You&apos;re on the list.</p>}

        <div className="my-6 flex items-center justify-between border-y border-paper/12 py-4">
          <p className="text-[10px] font-black uppercase tracking-[0.08em]">Follow along</p>
          <div className="flex gap-5 text-[18px] font-black"><span aria-label="Instagram">◎</span><span aria-label="TikTok">♪</span></div>
        </div>

        <p className="text-[11px] font-black uppercase tracking-[0.08em]">The whole curb crew</p>
        <div className="mt-4 grid grid-cols-6 gap-x-2 gap-y-4 sm:grid-cols-12">
          {CREATURES.map((c) => (
            // eslint-disable-next-line @next/next/no-img-element
            <img key={c.slug} src={creatureMaster(c.slug)} alt="" aria-hidden="true" className="h-8 w-full object-contain brightness-0 invert opacity-85 sm:h-9" />
          ))}
        </div>
        <div className="mt-6 flex items-center justify-between gap-4">
          <p className="text-[10px] font-black uppercase text-paper/60 sm:text-[12px]">More weirdos coming soon...</p>
          <Link href="/#crew" className="press inline-flex shrink-0 rounded-md bg-grit-green px-4 py-3 text-[9px] font-black uppercase text-ink sm:text-[11px]">Meet them all</Link>
        </div>
      </div>
    </section>
  );
}
