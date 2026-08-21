/**
 * Emails cart-recovery messages for pending orders abandoned an hour or more
 * ago — see notifyAbandonedOrders in store-queries.ts for the actual
 * selection and send logic. Run with `npm run notify:abandoned-orders`.
 *
 * This repo has no in-process job scheduler, so nothing calls this on its
 * own — it needs a cron entry on the box, e.g. hourly:
 *   0 * * * * cd /home/ubuntu/shirtfaced-admin && npx tsx src/db/notify-abandoned-orders.ts >> /var/log/shirtfaced-abandoned-cart.log 2>&1
 *
 * Same fallback behaviour as sync-approved-designs.ts and the email senders
 * themselves: a missing RESEND_API_KEY/RESEND_FROM_EMAIL means
 * sendAbandonedCartEmail silently no-ops per order rather than failing the
 * run, so this is safe to schedule before Resend is actually configured.
 */
import { config } from "dotenv";
import { notifyAbandonedOrders } from "./store-queries";

config({ path: ".env", override: true });

const SCRIPT = "notify-abandoned-orders";

notifyAbandonedOrders()
  .then((sent) => {
    console.log(`${SCRIPT}: sent ${sent} recovery email(s).`);
    process.exit(0);
  })
  .catch((error) => {
    console.error(`${SCRIPT}: failed`, error);
    process.exit(1);
  });
