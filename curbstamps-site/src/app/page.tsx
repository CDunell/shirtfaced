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

export default function HomePage() {
  return (
    <div className="overflow-hidden">
      <HeroWeirdo />
      <NewDropStrip />
      <TrustStrip />
      <CurbCrewScene />
      <PlayInvitation />
      <FindWeirdo />
      <ShopByCategory />
      <WeirdoMatch />
      <AdventureGrid />
      <ParentsCorner />
      <NewsletterJoin />
    </div>
  );
}
