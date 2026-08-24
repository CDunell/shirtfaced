import Link from "next/link";
import { GarmentArt } from "@/components/GarmentArt";
import { IconHeart, IconShield, IconSmile, IconTruck } from "@/components/Icons";
import { CREATURES, creatureMaster } from "@/lib/creatures";
import { getProduct } from "@/lib/products";
import type { HomepagePhoto } from "@/lib/homepage-photos";
import { CurbWorld } from "./CurbWorld";

const FAVOURITES = CREATURES.filter((creature) => creature.slug !== "dreg").slice(0, 10);
const PARADE = CREATURES.filter((creature) => creature.slug !== "dreg").slice(0, 18);

const CATEGORY_BLOCKS = [
  { eyebrow: "Just landed", title: "New drop", href: "/shop", cta: "Shop new", tone: "cream" },
  { eyebrow: "Everyday weird", title: "Tees", href: "/products/tee", cta: "Shop tees", tone: "tan" },
  { eyebrow: "Cold curb club", title: "Hoodies", href: "/products/hoodie", cta: "Shop hoodies", tone: "violet" },
  { eyebrow: "Top it off", title: "Accessories", href: "/products/bucket-hat", cta: "Shop hats", tone: "cream" },
] as const;

const TRUST = [
  { icon: IconHeart, title: "Soft stuff", body: "Made for all-day wear." },
  { icon: IconShield, title: "Built for play", body: "Tough enough for the curb." },
  { icon: IconTruck, title: "Tracked delivery", body: "Packed carefully. Sent quickly." },
  { icon: IconSmile, title: "Parent approved", body: "The useful details are easy to find." },
] as const;

function StreetCreature({ slug, className = "" }: { slug: string; className?: string }) {
  return (
    <span className={`street-creature ${className}`} aria-hidden="true">
      {/* eslint-disable-next-line @next/next/no-img-element */}
      <img src={`/curbstamps/world/creatures/${slug}.svg?v=20260824c`} alt="" />
    </span>
  );
}

function ProductFeature({
  title,
  body,
  href,
  cta,
  photo,
  creature,
  dark = false,
}: {
  title: string;
  body: string;
  href: string;
  cta: string;
  photo?: HomepagePhoto;
  creature: string;
  dark?: boolean;
}) {
  const product = getProduct(`${creature}-tee`)!;

  return (
    <article className={`commerce-card ${dark ? "commerce-card-dark" : ""}`}>
      <div className="commerce-copy">
        <p className="home-kicker">{body}</p>
        <h2 className="display home-card-title">{title}</h2>
        <Link href={href} className={`home-text-link ${dark ? "text-paper" : "text-ink"}`}>
          {cta} <span aria-hidden="true">→</span>
        </Link>
      </div>
      <div className="commerce-media">
        {photo ? (
          // eslint-disable-next-line @next/next/no-img-element
          <img src={photo.src} alt={photo.alt} className="commerce-photo" />
        ) : (
          <GarmentArt
            category="tee"
            bodyColour={product.colours[dark ? 0 : 1].body}
            art={product.art}
            artDark={product.artDark}
            creatureName={product.name}
            className="h-full rounded-none border-0"
          />
        )}
      </div>
    </article>
  );
}

export function CurbHomepage({ photos }: { photos: HomepagePhoto[] }) {
  const [arrivalPhoto, wantedPhoto, ...adventurePhotos] = photos;

  return (
    <div className="home-v2" data-home-version="curb-club-v1">
      <section className="home-grain home-hero" aria-labelledby="home-title">
        {/* eslint-disable-next-line @next/next/no-img-element */}
        <img src="/curbstamps/home-v2/splat-violet.webp" alt="" className="hero-splat" aria-hidden="true" />
        {/* eslint-disable-next-line @next/next/no-img-element */}
        <img src="/curbstamps/home-v2/sticker-cluster.webp" alt="" className="hero-stickers" aria-hidden="true" />

        <div className="home-shell hero-copy">
          <p className="home-kicker">Little weirdos. Big personalities.</p>
          <h1 id="home-title" className="display hero-title">Welcome to<br />the curb.</h1>
          <p className="hero-body">We found these weirdos outside. Now they live here with us.</p>
          <div className="hero-actions">
            <Link href="/shop" className="home-button home-button-ink">Shop the creatures</Link>
            <Link href="#crew" className="home-button home-button-acid">Meet them all</Link>
          </div>
        </div>

        <div className="hero-street" aria-hidden="true">
          <div className="hero-street-track">
            {/* eslint-disable-next-line @next/next/no-img-element */}
            <img src="/curbstamps/world/panels/01.webp?v=20260824a" alt="" />
            {/* eslint-disable-next-line @next/next/no-img-element */}
            <img src="/curbstamps/world/panels/02.webp?v=20260824a" alt="" />
          </div>
          <div className="home-shell hero-creature-layer">
            <StreetCreature slug="blip" className="hero-creature hero-creature-1" />
            <StreetCreature slug="squib" className="hero-creature hero-creature-2" />
            <StreetCreature slug="bub" className="hero-creature hero-creature-3" />
            <StreetCreature slug="lod" className="hero-creature hero-creature-4" />
            <StreetCreature slug="snu" className="hero-creature hero-creature-5" />
          </div>
        </div>
      </section>

      <section className="favourites-band" aria-labelledby="favourites-title">
        <div className="home-shell">
          <div className="section-heading-row">
            <div>
              <p className="home-kicker">Pick your local</p>
              <h2 id="favourites-title" className="display section-title">Who&apos;s your favourite?</h2>
            </div>
            <Link href="/shop" className="home-text-link favourites-all-link">See the whole crew →</Link>
          </div>
          <div className="favourites-scroll no-scrollbar">
            {FAVOURITES.map((creature, index) => (
              <Link key={creature.slug} href={`/products/tee?design=${creature.slug}`} className="favourite-card">
                <span className={`favourite-art favourite-tone-${index % 4}`}>
                  {/* eslint-disable-next-line @next/next/no-img-element */}
                  <img src={creatureMaster(creature.slug)} alt="" aria-hidden="true" />
                </span>
                <span className="favourite-name">{creature.name}</span>
              </Link>
            ))}
          </div>
        </div>
      </section>

      <section className="commerce-section home-grain" aria-label="New arrivals and most wanted">
        <div className="home-shell commerce-grid">
          <ProductFeature
            title="New arrivals"
            body="Fresh weirdos just landed"
            href="/shop"
            cta="Shop new"
            photo={arrivalPhoto}
            creature="blip"
          />
          <ProductFeature
            title="Most wanted"
            body="The curb legends"
            href="/products/tee?design=plod"
            cta="Shop best sellers"
            photo={wantedPhoto}
            creature="plod"
            dark
          />
        </div>
      </section>

      <section className="adopt-strip">
        <div className="home-shell adopt-inner">
          <div>
            <p className="home-kicker">They&apos;re house-trained. Mostly.</p>
            <h2 className="display section-title">Adopt a weirdo.</h2>
          </div>
          <div className="adopt-creatures" aria-hidden="true">
            {PARADE.slice(0, 6).map((creature) => (
              // eslint-disable-next-line @next/next/no-img-element
              <img key={creature.slug} src={creatureMaster(creature.slug)} alt="" />
            ))}
          </div>
          <Link href="/shop" className="home-button home-button-ink">Find yours</Link>
        </div>
      </section>

      <section className="category-section home-grain" aria-labelledby="category-title">
        <div className="home-shell">
          <p className="home-kicker">Wear your weirdo</p>
          <h2 id="category-title" className="display section-title section-title-large">Choose your thing.</h2>
          <div className="category-grid">
            {CATEGORY_BLOCKS.map((category, index) => (
              <Link key={category.title} href={category.href} className={`category-card category-${category.tone}`}>
                <p className="home-kicker">{category.eyebrow}</p>
                <h3 className="display category-title">{category.title}</h3>
                <span className="home-text-link">{category.cta} →</span>
                {/* eslint-disable-next-line @next/next/no-img-element */}
                <img src={creatureMaster(FAVOURITES[index + 1].slug)} alt="" aria-hidden="true" />
              </Link>
            ))}
          </div>
        </div>
      </section>

      <section className="trust-strip">
        <div className="home-shell trust-grid">
          {TRUST.map(({ icon: Icon, title, body }) => (
            <div key={title} className="trust-item">
              <Icon className="trust-icon" />
              <div><h3>{title}</h3><p>{body}</p></div>
            </div>
          ))}
        </div>
      </section>

      <section id="crew" className="crew-section home-grain" aria-labelledby="crew-title">
        <div className="home-shell">
          <div className="section-heading-row crew-heading">
            <div>
              <p className="home-kicker">Their side of town</p>
              <h2 id="crew-title" className="display section-title section-title-large">Meet the curb crew.</h2>
              <p className="section-copy">Take a wander down the street they call home. The crew are moving in one by one.</p>
            </div>
            <Link href="/shop" className="home-button home-button-acid">Shop the crew</Link>
          </div>
          <CurbWorld />
          <div className="crew-bottom-link">
            <Link href="/shop" className="home-text-link">Shop street locals →</Link>
          </div>
        </div>
      </section>

      <section className="adventure-section" aria-labelledby="adventure-title">
        <div className="home-shell">
          <p className="home-kicker">Clothes that leave the house</p>
          <h2 id="adventure-title" className="display section-title section-title-large">Made for adventures.</h2>
          <div className="adventure-grid">
            {["Play", "Explore", "Make", "Be weird"].map((label, index) => {
              const photo = adventurePhotos[index];
              const creature = ["squib", "snu", "nub", "claw"][index];
              return (
                <Link key={label} href={`/products/tee?design=${creature}`} className="adventure-card">
                  {photo ? (
                    // eslint-disable-next-line @next/next/no-img-element
                    <img src={photo.src} alt={photo.alt} />
                  ) : (
                    <div className="adventure-placeholder" />
                  )}
                  <h3 className="display">{label}</h3>
                </Link>
              );
            })}
          </div>
          <Link href="/shop" className="home-button home-button-ink adventure-cta">Shop clothes made for play</Link>
        </div>
      </section>

      <section className="parents-section home-grain" aria-labelledby="parents-title">
        <div className="home-shell parents-grid">
          <div>
            <p className="home-kicker">The useful bit</p>
            <h2 id="parents-title" className="display section-title section-title-large">Parents corner.</h2>
            <p className="section-copy">Sizing, delivery and care—easy to find, easy to understand.</p>
          </div>
          <div className="parents-links">
            <Link href="/size-guide"><strong>Sizes 2–10</strong><span>Find the right fit →</span></Link>
            <Link href="/shipping"><strong>Shipping</strong><span>Where it is and when it lands →</span></Link>
            <Link href="/garment-care"><strong>Easy care</strong><span>Wash, wear, repeat →</span></Link>
            <Link href="/contact"><strong>Need help?</strong><span>Talk to a human →</span></Link>
          </div>
        </div>
      </section>

      <section id="club" className="club-section" aria-labelledby="club-title">
        {/* eslint-disable-next-line @next/next/no-img-element */}
        <img src="/curbstamps/home-v2/splat-violet.webp" alt="" className="club-splat" aria-hidden="true" />
        <div className="home-shell club-inner">
          <div className="club-copy">
            <p className="home-kicker">New drops. Strange locals. No boring emails.</p>
            <h2 id="club-title" className="display club-title">Curb club.</h2>
            <form className="club-form" action="#" method="post">
              <label htmlFor="club-email" className="sr-only">Email address</label>
              <input id="club-email" name="email" type="email" required placeholder="Your email" />
              <button type="submit">Join up</button>
            </form>
            <Link href="/shop" className="home-text-link club-shop-link">Shop the whole curb →</Link>
          </div>
          {/* eslint-disable-next-line @next/next/no-img-element */}
          <img src="/curbstamps/home-v2/sticker-cluster.webp" alt="" className="club-stickers" aria-hidden="true" />
        </div>
        <div className="home-shell club-parade" aria-hidden="true">
          {PARADE.map((creature) => (
            // eslint-disable-next-line @next/next/no-img-element
            <img key={creature.slug} src={creatureMaster(creature.slug)} alt="" />
          ))}
        </div>
      </section>
    </div>
  );
}
