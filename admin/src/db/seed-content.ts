/**
 * One-time import of the storefront's current hardcoded page copy into
 * Postgres, verbatim, so switching the pages over to DB-sourced content
 * doesn't change anything visually. Run with `npm run seed:content`.
 * Safe to re-run — each page is a single upserted row (id=1).
 */
import { db } from "./client";
import {
  aboutContent,
  shippingContent,
  returnsContent,
  contactContent,
  sizeGuideContent,
  homeContent,
  moreContent,
  productPageContent,
  accountContent,
  garmentCareContent,
  faqContent,
  faqItems,
} from "./schema";

const about = {
  id: 1,
  intro:
    "shirtfaced makes graphic tees for people with questionable judgement and excellent taste. That's the entire brief.",
  ideaP1:
    "Most graphic tees are either forgettable or trying far too hard. We wanted the ones you actually reach for — heavy cotton, cut wide, printed with something worth reading from across a room.",
  ideaP2:
    "Every design starts as a joke someone refused to let go of. If it still lands a month later, it gets printed.",
  howMadeP1:
    "220gsm combed cotton, structured fit, dropped shoulder. Designed in Australia and screen-printed by specialists wherever that gets it to you fastest — the design is ours, the press is whoever does it properly.",
  howMadeP2:
    "Prints are built to crack and fade the way a good tee should. It will look better in a year than it does in the bag.",
  wontDoP1:
    "No countdown timers telling you four people are looking at this right now. No fake scarcity. No inventing an origin story we can't back up.",
  whoP1:
    "A small Australian outfit that started in 2026 and has so far made exactly the decisions you'd expect from people who named a company this.",
};

const shipping = {
  id: 1,
  intro:
    "Designed in Australia, printed and shipped from wherever gets it to you fastest.",
  standardName: "Standard",
  standardTime: "2–6 business days",
  standardPrice: "$11.70",
  expressName: "Express",
  expressTime: "1–3 business days",
  expressPrice: "$15.20",
  whereP1:
    "Australia-wide, including WA and the Territories. New Zealand ships at a flat $21.60 and takes 4–7 business days.",
  whereP2:
    "Everywhere else — we're working on it. If you're overseas and desperate, get in touch and we'll quote you properly rather than guess.",
  trackingP1:
    "Every order gets a tracking number by email the moment it leaves. If it hasn't arrived within the window above, tell us and we'll chase it — you shouldn't have to argue with a courier on our behalf.",
  packagingP1:
    "Recycled mailers, no plastic filler, no branded tissue paper that goes straight in the bin. The mailer is the packaging.",
};

const returns = {
  id: 1,
  intro: "Thirty days. Unworn, unwashed, tags on. We won't ask why.",
  step1Title: "Email us",
  step1Body: "Order number and which items are coming back. That's the whole form.",
  step2Title: "We send a label",
  step2Body: "Prepaid, within one business day.",
  step3Title: "Post it",
  step3Body: "Any Australia Post box. Keep the receipt until it's refunded.",
  step4Title: "Refunded",
  step4Body: "Back to your original payment method within 5 business days of arrival.",
  exchangesP1:
    "Wrong size is the usual one. Return it and order the right size — it's faster than a formal exchange and you're not waiting on our stock check.",
  exchangesP2:
    "If the size you want has sold out in the meantime, tell us and we'll hold one from the next run.",
  wrongP1:
    "Faulty print, dodgy stitching, wrong item in the bag — send a photo and we'll replace it, no return needed. That's our mistake, not your errand.",
  wrongP2:
    "This sits alongside your rights under Australian Consumer Law, which nothing here limits.",
  cantTakeP1:
    "Worn or washed items, and anything returned after 30 days. Not because we're precious — we just can't resell it and won't pretend otherwise.",
};

const contact = {
  id: 1,
  intro:
    "A real person reads these, usually within one business day. Weekends are a gamble.",
  email: "hello@shirtfaced.wtf",
  wholesaleP1:
    'If you run a shop and want these on a rack, email the same address with "wholesale" in the subject and we\'ll send a line sheet.',
  pressP1:
    "Also the same address. We're not big enough for separate inboxes and pretending otherwise would be embarrassing.",
  bottomBlurb: "nice shirt. shame about your choices.",
};

const sizeGuide = {
  id: 1,
  intro:
    "Everything is cut boxy and slightly oversized. If you want it fitted, size down. If you want it huge, you're already thinking correctly.",
  measureChest:
    "lay the tee flat, measure straight across one centimetre below the armhole, seam to seam. That's a half-chest measurement, so double it to compare against a body measurement.",
  measureLength: "from the highest point of the shoulder straight down to the hem.",
  betweenSizesP1:
    "Size up. These are meant to sit wide with a dropped shoulder, and nobody has ever complained that a tee was too comfortable.",
  betweenSizesP2:
    "Measurements are taken flat and have a tolerance of about a centimetre either way, because they're cut and sewn by people rather than robots.",
  careP1:
    "Cold wash, inside out, hang dry. Don't iron the print unless you want it to become someone else's problem.",
  sChest: "48–50cm",
  sLength: "68cm",
  mChest: "51–53cm",
  mLength: "72cm",
  lChest: "54–56cm",
  lLength: "75cm",
  xlChest: "57–59cm",
  xlLength: "78cm",
  xxlChest: "60–62cm",
  xxlLength: "81cm",
};

const home = {
  id: 1,
  trust1: "Designed in Aus",
  trust2: "Zero apologies",
  trust3: "Returns easy as",
  promoHeading: "dress like you've got better plans.",
  promoAlt: "Model wearing the Send It Club tee in vintage white",
  newsletterHeading: "we promise fewer emails than your ex.",
};

const more = {
  id: 1,
  blurbHeading: "bad financial decisions since 2026",
  blurbSubline: "Designed in Australia. Printed properly. Worn badly.",
};

const productPage = {
  id: 1,
  feature1A: "100% combed cotton",
  feature1B: "built for adventures",
  feature2A: "220gsm mid weight",
  feature2B: "holds its shape",
  feature3A: "designed in australia",
  feature3B: "printed worldwide",
  feature4A: "easy returns",
  feature4B: "no drama",
};

const account = {
  id: 1,
  intro:
    "Accounts aren't open yet. You can still track an order — that's the only bit anyone actually wants.",
  benefit1A: "Order history",
  benefit1B: "Everything you've regretted, itemised",
  benefit2A: "Faster checkout",
  benefit2B: "Saved address, no retyping",
  benefit3A: "Early access",
  benefit3B: "Drops before they go public",
};

const garmentCare = {
  id: 1,
  intro:
    "Two fabrics, same rule: treat the print like it matters, because it's the whole point.",
  washingP1:
    "Cold wash, inside out, similar colours only. The garment-dyed pieces (anything in Comfort Colors) will keep fading and softening on purpose — that's not a fault, that's the finish doing its job.",
  dryingP1:
    "Hang dry where you can. A dryer won't ruin it outright, but heat is what ages a print fastest, and you paid for the print.",
  printCareP1:
    "Don't iron directly on it, don't dry-clean it, and don't scrub a stain into the ink. Cold water, mild detergent, patience.",
  storageP1:
    "Fold it, don't hang it. Hanging a heavy cotton tee by the shoulders stretches the neckline over time — folding doesn't.",
};

const faq = {
  id: 1,
  intro: "The questions that come up before the ones that come up after.",
};

const faqItemRows = [
  {
    question: "What are shirtfaced tees actually made from?",
    answer:
      "The main range is AS Colour 5026 — 220gsm combed cotton, regular structured fit. Washed and vintage-led releases use Comfort Colors 1717 — around 207gsm ring-spun cotton, garment-dyed, relaxed fit. Different garment, different job.",
    sortOrder: 0,
  },
  {
    question: "What size should I get?",
    answer:
      "Everything's cut boxy and slightly oversized. If you want it fitted, size down. Full measurements:",
    linkHref: "/size-guide",
    linkLabel: "size guide",
    sortOrder: 1,
  },
  {
    question: "How long does shipping take?",
    answer:
      "Rates and timeframes change, so we keep one accurate copy of it rather than duplicating it here:",
    linkHref: "/shipping",
    linkLabel: "shipping",
    sortOrder: 2,
  },
  {
    question: "Do you ship outside Australia?",
    answer:
      "New Zealand, yes. Further than that, we're working on it — get in touch and we'll quote you properly rather than guess.",
    sortOrder: 3,
  },
  {
    question: "What's the returns policy?",
    answer:
      "Faulty or wrong item — send a photo, we replace it, no return needed. For everything else, the window and process are on the",
    linkHref: "/returns",
    linkLabel: "returns page",
    sortOrder: 4,
  },
  {
    question: "How do I wash it without wrecking the print?",
    answer: "Cold wash, inside out, hang dry, don't iron the print. Full detail:",
    linkHref: "/garment-care",
    linkLabel: "garment care",
    sortOrder: 5,
  },
  {
    question: "Do you do wholesale?",
    answer:
      'Email us with "wholesale" in the subject and we\'ll send a line sheet.',
    sortOrder: 6,
  },
];

function omitId<T extends { id: number }>(row: T): Omit<T, "id"> {
  const { id: _id, ...rest } = row;
  return rest;
}

async function main() {
  await db.insert(aboutContent).values(about).onConflictDoUpdate({
    target: aboutContent.id,
    set: omitId(about),
  });
  await db.insert(shippingContent).values(shipping).onConflictDoUpdate({
    target: shippingContent.id,
    set: omitId(shipping),
  });
  await db.insert(returnsContent).values(returns).onConflictDoUpdate({
    target: returnsContent.id,
    set: omitId(returns),
  });
  await db.insert(contactContent).values(contact).onConflictDoUpdate({
    target: contactContent.id,
    set: omitId(contact),
  });
  await db.insert(sizeGuideContent).values(sizeGuide).onConflictDoUpdate({
    target: sizeGuideContent.id,
    set: omitId(sizeGuide),
  });
  await db.insert(homeContent).values(home).onConflictDoUpdate({
    target: homeContent.id,
    set: omitId(home),
  });
  await db.insert(moreContent).values(more).onConflictDoUpdate({
    target: moreContent.id,
    set: omitId(more),
  });
  await db.insert(productPageContent).values(productPage).onConflictDoUpdate({
    target: productPageContent.id,
    set: omitId(productPage),
  });
  await db.insert(accountContent).values(account).onConflictDoUpdate({
    target: accountContent.id,
    set: omitId(account),
  });
  await db.insert(garmentCareContent).values(garmentCare).onConflictDoUpdate({
    target: garmentCareContent.id,
    set: omitId(garmentCare),
  });
  await db.insert(faqContent).values(faq).onConflictDoUpdate({
    target: faqContent.id,
    set: omitId(faq),
  });

  // faqItems is a real list, not a singleton — re-seeding replaces the set
  // rather than upserting by id, since there's no natural key to match on.
  await db.delete(faqItems);
  await db.insert(faqItems).values(faqItemRows);

  console.log(
    "Seeded site content (about, shipping, returns, contact, size guide, home, more, product page, account, garment care, faq).",
  );
  process.exit(0);
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
