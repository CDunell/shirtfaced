import { drizzle } from "drizzle-orm/postgres-js";
import postgres from "postgres";
import { config } from "dotenv";
import * as schema from "./schema";

// Next.js loads .env itself for `next dev`/`build`/`start`; this is a no-op
// there (the vars are already set) but is required for standalone scripts
// run via tsx (e.g. the seed script). override:true because this machine has
// an unrelated, persistently-set OS-level DATABASE_URL from another project —
// see drizzle.config.ts for the full story. SHOP_DATABASE_URL itself doesn't
// collide with anything, override is just a second line of defence.
config({ path: ".env", override: true });

const connectionString = process.env.SHOP_DATABASE_URL;
if (!connectionString) {
  throw new Error("SHOP_DATABASE_URL is not set");
}

const queryClient = postgres(connectionString);
export const db = drizzle(queryClient, { schema });
