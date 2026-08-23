import { HeroWeirdo } from "@/components/home/HeroWeirdo";
import { NewDropStrip } from "@/components/home/NewDropStrip";
import { CurbCrewScene } from "@/components/home/CurbCrewScene";
import { FindWeirdo } from "@/components/home/FindWeirdo";
import { ShopByCategory } from "@/components/home/ShopByCategory";
import { TrustStrip } from "@/components/home/TrustStrip";
import { WeirdoMatch } from "@/components/home/WeirdoMatch";
import { AdventureGrid } from "@/components/home/AdventureGrid";
import { ParentsCorner } from "@/components/home/ParentsCorner";
import { NewsletterJoin } from "@/components/home/NewsletterJoin";
import { PlayInvitation } from "@/components/home/PlayInvitation";
import { pickHomepagePhotos } from "@/lib/homepage-photos";

// Homepage photo rotation needs to actually vary between visits, not freeze
// at whatever pickHomepagePhotos() returned the moment this page was first
// statically generated — see docs/curbstamps/CURBSTAMPS_DEPLOYMENT.md for
// the .next/cache staleness issue this same class of bug caused elsewhere.
export const dynamic = "force-dynamic";

export default function HomePage() {
  const [dropA, dropB, shopPhoto, ...adventurePhotos] = pickHomepagePhotos(7);

  return (
    <div className="overflow-hidden">
      <HeroWeirdo />
      <NewDropStrip photos={[dropA, dropB]} />
      <TrustStrip />
      <CurbCrewScene />
      <PlayInvitation />
      <FindWeirdo />
      <ShopByCategory photo={shopPhoto} />
      <WeirdoMatch />
      <AdventureGrid photos={adventurePhotos} />
      <ParentsCorner />
      <NewsletterJoin />
    </div>
  );
}
