import { config } from "dotenv";
import postgres from "postgres";

config({ path: ".env" });

const connectionString = process.env.SHOP_DATABASE_URL;
if (!connectionString) {
  throw new Error("SHOP_DATABASE_URL is required");
}

const sql = postgres(connectionString);

/* Top-level await needs an ESM module context; admin/package.json has no
   "type": "module", so tsx (run directly via npm's build script, not through
   Next.js's own bundler) treats this file as CommonJS and rejects a bare
   top-level await. Wrapping in an async IIFE, called without awaiting it at
   the top level, sidesteps that without touching the whole project's module
   type. Node's default unhandled-rejection behaviour (crash with the error)
   still makes a failed migration fail the build loudly, which is the point. */
void (async () => {
  try {
    await sql.begin(async (tx) => {
      await tx`
        UPDATE returns_content
        SET
          intro = ${"Choose carefully. We don't do change-of-mind returns because you got home and decided the vibe was wrong."},
          step1_title = ${"Check the size guide"},
          step1_body = ${"Before you order. Measure a tee you already own if you have to. Future you will appreciate the effort."},
          step2_title = ${"Order the one you actually want"},
          step2_body = ${"Wrong size, wrong colour or changed your mind isn't a return reason. That's the deal."},
          step3_title = ${"Something actually wrong?"},
          step3_body = ${"Fault, damage, wrong item or something that doesn't match what we sold you — email us with your order number and a photo."},
          step4_title = ${"We'll sort our shit out"},
          step4_body = ${"If we've stuffed it, we'll provide the remedy you're entitled to under Australian Consumer Law. No bullshit obstacle course."},
          exchanges_p1 = ${"We don't offer exchanges for change of mind, including ordering the wrong size or colour. Check the size guide before committing."},
          exchanges_p2 = ${"If there's a genuine problem with the garment, that's different. Get in touch and we'll sort it properly."},
          wrong_p1 = ${"Faulty print, dodgy stitching, damaged garment, wrong item in the bag, or something that doesn't match its description — send your order number and a photo to hello@shirtfaced.wtf."},
          wrong_p2 = ${"Your rights under Australian Consumer Law still apply. This policy doesn't remove, limit or replace them. If the law says you're entitled to a repair, replacement, refund or other remedy, that's what applies."},
          cant_take_p1 = ${"We don't accept returns because you changed your mind, picked the wrong size, picked the wrong colour, found something else you like more, or your mate said it looked shit. Genuine faults and your Australian Consumer Law rights are a different story."}
        WHERE id = 1
          AND intro = ${"Thirty days. Unworn, unwashed, tags on. We won't ask why."}
      `;

      await tx`
        UPDATE home_content
        SET trust3 = ${"No change-of-mind returns"}
        WHERE id = 1 AND trust3 = ${"Returns easy as"}
      `;

      await tx`
        UPDATE product_page_content
        SET feature4_a = ${"choose carefully"}, feature4_b = ${"no change-of-mind returns"}
        WHERE id = 1
          AND feature4_a = ${"easy returns"}
          AND feature4_b = ${"no drama"}
      `;

      await tx`
        UPDATE faq_items
        SET answer = ${"No change-of-mind returns. If it's faulty, damaged, wrong or not as described, we'll sort it in line with Australian Consumer Law. Full detail:"}
        WHERE question = ${"What's the returns policy?"}
          AND answer = ${"Faulty or wrong item — send a photo, we replace it, no return needed. For everything else, the window and process are on the"}
      `;
    });

    console.log("returns-policy migration applied (legacy values only)");
  } finally {
    await sql.end();
  }
})();
