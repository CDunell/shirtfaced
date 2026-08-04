import { defineConfig } from "drizzle-kit";
import { config } from "dotenv";

// override: true is load-bearing — this machine has an unrelated,
// persistently-set DATABASE_URL in the OS environment (a different project).
// dotenv (and Next's own env loader) refuse to override existing process.env
// values by default, so a generic name would silently point at the wrong
// database. SHOP_DATABASE_URL avoids the collision; override:true is a second
// line of defence.
config({ path: ".env", override: true });

export default defineConfig({
  schema: "./src/db/schema.ts",
  out: "./src/db/migrations",
  dialect: "postgresql",
  dbCredentials: {
    url: process.env.SHOP_DATABASE_URL!,
  },
});
