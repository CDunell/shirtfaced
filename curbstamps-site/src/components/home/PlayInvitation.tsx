import Link from "next/link";
import { creatureMaster } from "@/lib/creatures";

export function PlayInvitation() {
  return (
    <section className="bg-grit-lilac px-4 py-9 sm:px-6 sm:py-12">
      <Link href="/play" className="press mx-auto grid max-w-5xl grid-cols-[1fr_108px] items-center overflow-hidden rounded-[24px] border-2 border-ink bg-grit-yellow p-5 shadow-[6px_6px_0_#1c1a17] sm:grid-cols-[1fr_230px] sm:p-8">
        <div>
          <p className="mb-2 text-[10px] font-black uppercase tracking-[0.15em]">New! Play on the Curb</p>
          <h2 className="display text-[11vw] uppercase leading-[0.88] sm:text-[58px]">make some<br />weirdo noise!</h2>
          <span className="mt-4 inline-flex min-h-11 items-center rounded-full border-2 border-ink bg-ink px-5 text-[13px] font-black uppercase text-cream">Come play →</span>
        </div>
        {/* eslint-disable-next-line @next/next/no-img-element */}
        <img src={creatureMaster("fizz")} alt="Fizz" className="w-full rotate-[-5deg] brightness-0" />
      </Link>
    </section>
  );
}
