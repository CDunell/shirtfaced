import { CurbHomepage } from "@/components/home/CurbHomepage";
import { pickHomepagePhotos } from "@/lib/homepage-photos";

// Homepage photo rotation needs to actually vary between visits, not freeze
// at whatever pickHomepagePhotos() returned the moment this page was first
// statically generated — see docs/curbstamps/CURBSTAMPS_DEPLOYMENT.md for
// the .next/cache staleness issue this same class of bug caused elsewhere.
export const dynamic = "force-dynamic";

export default function HomePage() {
  const photos = pickHomepagePhotos(6);

  return (
    <CurbHomepage photos={photos} />
  );
}
