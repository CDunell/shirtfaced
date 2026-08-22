import { HeroWeirdo } from "@/components/home/HeroWeirdo";
import { NewDropStrip } from "@/components/home/NewDropStrip";
import { TrustStrip } from "@/components/home/TrustStrip";
import { CurbCrewScene } from "@/components/home/CurbCrewScene";
import { ShopByCategory } from "@/components/home/ShopByCategory";
import { WeirdoMatch } from "@/components/home/WeirdoMatch";
import { AdventureGrid } from "@/components/home/AdventureGrid";
import { ParentsCorner } from "@/components/home/ParentsCorner";
import { NewsletterJoin } from "@/components/home/NewsletterJoin";

/**
 * Homepage — built from DESIGN_HANDOFF.md's approved storyboard (§4, sections
 * B through K). Section F, "FIND YOUR WEIRDO" (the hidden-creature mini-game),
 * is deliberately not built yet — the handoff's own build order (§12) puts it
 * last, after every other section is live. Admin fields for this page (§10)
 * are the step after that, once the visual homepage itself is approved.
 */
export default function HomePage() {
  return (
    <>
      <HeroWeirdo />
      <NewDropStrip />
      <TrustStrip />
      <CurbCrewScene />
      <ShopByCategory />
      <WeirdoMatch />
      <AdventureGrid />
      <ParentsCorner />
      <NewsletterJoin />
    </>
  );
}
