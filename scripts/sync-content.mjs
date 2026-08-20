#!/usr/bin/env node
/**
 * Pulls site page copy (About/Shipping/Returns/Contact/Size guide) from
 * Postgres and writes it to src/lib/content-data.generated.ts. Same
 * no-op-without-SHOP_DATABASE_URL fallback behaviour as sync-products.mjs —
 * see that file for why.
 */
import { writeFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";
import { config } from "dotenv";
import postgres from "postgres";

const __dirname = dirname(fileURLToPath(import.meta.url));
config({ path: join(__dirname, "..", ".env") });

const connectionString = process.env.SHOP_DATABASE_URL;
const outFile = join(
  __dirname,
  "..",
  "src",
  "lib",
  "content-data.generated.ts",
);

if (!connectionString) {
  console.log(
    "sync-content: SHOP_DATABASE_URL not set, skipping — using the committed snapshot as-is.",
  );
  process.exit(0);
}

const SCRIPT = "sync-content";
/**
 * The guard above catches a missing variable. It does not catch a variable that
 * is set and unreachable, which is the ordinary case on a dev machine: the URL
 * is committed in .env and points at 127.0.0.1:55432, an SSH tunnel to the shop
 * database that is only up when somebody opened it.
 *
 * Without this the script hard-fails on ECONNREFUSED and takes `npm run dev`
 * with it, so the site cannot be run at all -- including to change a line of
 * static copy that has nothing to do with the database. Unreachable is treated
 * the same as unconfigured: fall back to the committed snapshot and say so.
 */
async function reachable(sql) {
  try {
    await sql`SELECT 1`;
    return true;
  } catch (error) {
    const why = error.code || error.message;

    // Falling back is right on a dev machine and wrong on the box. Production
    // builds against a database local to the server, so unreachable there means
    // something is broken -- and quietly shipping the last committed snapshot
    // would publish stale prices and a stale catalogue with nothing to show for
    // it. Loud on the way out beats silent and wrong.
    if (process.env.NODE_ENV === "production" || process.env.CI) {
      throw new Error(
        `${SCRIPT}: cannot reach the shop database (${why}) during a production ` +
          "build. Refusing to publish the committed snapshot in its place.",
      );
    }

    console.log(
      `${SCRIPT}: cannot reach the shop database (${why}) — using the committed ` +
        "snapshot as-is. Open the SSH tunnel to refresh it.",
    );
    return false;
  }
}

const sql = postgres(connectionString);
if (!(await reachable(sql))) {
  await sql.end({ timeout: 1 });
  process.exit(0);
}

const [about] = await sql`SELECT * FROM about_content WHERE id = 1`;
const [shipping] = await sql`SELECT * FROM shipping_content WHERE id = 1`;
const [returns] = await sql`SELECT * FROM returns_content WHERE id = 1`;
const [contact] = await sql`SELECT * FROM contact_content WHERE id = 1`;
const [sizeGuide] = await sql`SELECT * FROM size_guide_content WHERE id = 1`;
const [home] = await sql`SELECT * FROM home_content WHERE id = 1`;
const [more] = await sql`SELECT * FROM more_content WHERE id = 1`;
const [productPage] =
  await sql`SELECT * FROM product_page_content WHERE id = 1`;
const [account] = await sql`SELECT * FROM account_content WHERE id = 1`;
const [garmentCare] =
  await sql`SELECT * FROM garment_care_content WHERE id = 1`;
const [faq] = await sql`SELECT * FROM faq_content WHERE id = 1`;
const faqItemRows =
  await sql`SELECT * FROM faq_items ORDER BY sort_order ASC`;

await sql.end();

const content = {
  about: {
    intro: about.intro,
    ideaP1: about.idea_p1,
    ideaP2: about.idea_p2,
    howMadeP1: about.how_made_p1,
    howMadeP2: about.how_made_p2,
    wontDoP1: about.wont_do_p1,
    whoP1: about.who_p1,
  },
  shipping: {
    intro: shipping.intro,
    standardName: shipping.standard_name,
    standardTime: shipping.standard_time,
    standardPrice: shipping.standard_price,
    expressName: shipping.express_name,
    expressTime: shipping.express_time,
    expressPrice: shipping.express_price,
    whereP1: shipping.where_p1,
    whereP2: shipping.where_p2,
    trackingP1: shipping.tracking_p1,
    packagingP1: shipping.packaging_p1,
  },
  returns: {
    intro: returns.intro,
    step1Title: returns.step1_title,
    step1Body: returns.step1_body,
    step2Title: returns.step2_title,
    step2Body: returns.step2_body,
    step3Title: returns.step3_title,
    step3Body: returns.step3_body,
    step4Title: returns.step4_title,
    step4Body: returns.step4_body,
    exchangesP1: returns.exchanges_p1,
    exchangesP2: returns.exchanges_p2,
    wrongP1: returns.wrong_p1,
    wrongP2: returns.wrong_p2,
    cantTakeP1: returns.cant_take_p1,
  },
  contact: {
    intro: contact.intro,
    email: contact.email,
    wholesaleP1: contact.wholesale_p1,
    pressP1: contact.press_p1,
    bottomBlurb: contact.bottom_blurb,
  },
  sizeGuide: {
    intro: sizeGuide.intro,
    measureChest: sizeGuide.measure_chest,
    measureLength: sizeGuide.measure_length,
    betweenSizesP1: sizeGuide.between_sizes_p1,
    betweenSizesP2: sizeGuide.between_sizes_p2,
    careP1: sizeGuide.care_p1,
    chart: {
      S: { chest: sizeGuide.s_chest, length: sizeGuide.s_length },
      M: { chest: sizeGuide.m_chest, length: sizeGuide.m_length },
      L: { chest: sizeGuide.l_chest, length: sizeGuide.l_length },
      XL: { chest: sizeGuide.xl_chest, length: sizeGuide.xl_length },
      XXL: { chest: sizeGuide.xxl_chest, length: sizeGuide.xxl_length },
    },
  },
  home: {
    trust1: home.trust1,
    trust2: home.trust2,
    trust3: home.trust3,
    promoHeading: home.promo_heading,
    promoAlt: home.promo_alt,
    newsletterHeading: home.newsletter_heading,
  },
  more: {
    blurbHeading: more.blurb_heading,
    blurbSubline: more.blurb_subline,
  },
  productPage: {
    features: [
      { a: productPage.feature1_a, b: productPage.feature1_b },
      { a: productPage.feature2_a, b: productPage.feature2_b },
      { a: productPage.feature3_a, b: productPage.feature3_b },
      { a: productPage.feature4_a, b: productPage.feature4_b },
    ],
  },
  account: {
    intro: account.intro,
    benefits: [
      { a: account.benefit1_a, b: account.benefit1_b },
      { a: account.benefit2_a, b: account.benefit2_b },
      { a: account.benefit3_a, b: account.benefit3_b },
    ],
  },
  garmentCare: {
    intro: garmentCare.intro,
    washingP1: garmentCare.washing_p1,
    dryingP1: garmentCare.drying_p1,
    printCareP1: garmentCare.print_care_p1,
    storageP1: garmentCare.storage_p1,
  },
  faq: {
    intro: faq.intro,
    items: faqItemRows.map((row) => ({
      question: row.question,
      answer: row.answer,
      linkHref: row.link_href,
      linkLabel: row.link_label,
    })),
  },
};

const banner = `/**
 * AUTO-GENERATED by scripts/sync-content.mjs — do not edit by hand.
 * Run \`npm run sync:content\` to refresh from the admin database.
 * Checked into git as a fallback snapshot for builds without DB access.
 */
`;

const body = Object.entries(content)
  .map(
    ([key, value]) =>
      `export const ${key} = ${JSON.stringify(value, null, 2)};`,
  )
  .join("\n\n");

writeFileSync(outFile, banner + "\n" + body + "\n");
console.log(`sync-content: wrote page content to ${outFile}`);
