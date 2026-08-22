import { defineConfig } from "drizzle-kit";
import { config } from "dotenv";

// override: true — same reasoning as shirtfaced-admin/drizzle.config.ts:
// some machines carry an unrelated, persistently-set DATABASE_URL from
// another project. CURBSTAMPS_DATABASE_URL avoids the name collision;
// override:true is a second line of defence.
config({ path: ".env", override: true });

export default defineConfig({
  schema: "./src/db/schema.ts",
  out: "./src/db/migrations",
  dialect: "postgresql",
  dbCredentials: {
    url: process.env.CURBSTAMPS_DATABASE_URL!,
  },
});
