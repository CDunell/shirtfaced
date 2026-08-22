"use client";

import { useState } from "react";
import { CREATURES } from "@/lib/creatures";

/**
 * Section K — "JOIN THE CURB" (DESIGN_HANDOFF.md §4.K). No mailing-list
 * provider is wired up yet (no Resend/Mailchimp/ConvertKit list id anywhere
 * in this app) — same honesty as checkout's "payment isn't connected"
 * state, rather than pretending to collect an email that goes nowhere.
 */
export function NewsletterJoin() {
  const [email, setEmail] = useState("");
  const [state, setState] = useState<"idle" | "not-configured">("idle");

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    // TODO: POST to a real mailing-list endpoint once one exists.
    setState("not-configured");
  }

  return (
    <section className="bg-ink text-paper">
      <div className="mx-auto max-w-5xl px-4 py-14 sm:px-6">
        <div className="mx-auto max-w-md text-center">
          <h2 className="display text-[11vw] leading-[0.9] sm:text-[38px]">join the curb!</h2>
          <p className="mt-2 text-[14px] text-paper/70">First to see new drops and special stuff.</p>

          <form onSubmit={handleSubmit} className="mt-6 flex gap-2">
            <label htmlFor="newsletter-email" className="sr-only">
              Email address
            </label>
            <input
              id="newsletter-email"
              type="email"
              required
              placeholder="you@email.com"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="h-13 min-w-0 flex-1 rounded-full border-2 border-paper/20 bg-transparent px-4 text-[15px] text-paper placeholder:text-paper/40"
            />
            <button
              type="submit"
              className="press h-13 shrink-0 rounded-full bg-grit-green px-6 text-[14px] font-extrabold text-ink"
            >
              Join
            </button>
          </form>
          {state === "not-configured" && (
            <p className="mt-3 text-[12px] text-paper/60">
              Signups aren&apos;t connected to a mailing list yet — this just confirmed the form works.
            </p>
          )}
        </div>

        <div className="no-scrollbar mt-14 flex gap-6 overflow-x-auto opacity-70">
          {CREATURES.map((c) => (
            // eslint-disable-next-line @next/next/no-img-element
            <img
              key={c.slug}
              src={`/curbstamps/creatures/${c.slug}-light.svg`}
              alt=""
              aria-hidden="true"
              className="h-10 w-16 shrink-0 object-contain"
            />
          ))}
        </div>
        <p className="mt-4 text-center text-[12px] font-bold text-paper/50">
          more weirdos coming soon...
        </p>
      </div>
    </section>
  );
}
