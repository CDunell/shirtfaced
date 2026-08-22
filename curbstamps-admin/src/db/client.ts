import { drizzle } from "drizzle-orm/postgres-js";
import postgres from "postgres";
import { config } from "dotenv";
import * as schema from "./schema";

// Next.js loads .env itself for `next dev`/`build`/`start`; this is a no-op
// there but required for standalone scripts run via tsx (seed.ts).
config({ path: ".env", override: true });

const connectionString = process.env.CURBSTAMPS_DATABASE_URL;
if (!connectionString) {
  throw new Error("CURBSTAMPS_DATABASE_URL is not set");
}

const queryClient = postgres(connectionString);
export const db = drizzle(queryClient, { schema });
