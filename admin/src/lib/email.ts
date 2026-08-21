import { Resend } from "resend";

export type OrderConfirmationItem = {
  productName: string;
  colourName: string | null;
  size: string | null;
  quantity: number;
  unitPriceCents: number;
};

export type OrderConfirmationInput = {
  toEmail: string;
  toName: string;
  reference: string;
  items: OrderConfirmationItem[];
  subtotalCents: number;
  shippingCents: number;
  totalCents: number;
};

function money(cents: number): string {
  return new Intl.NumberFormat("en-AU", { style: "currency", currency: "AUD" }).format(cents / 100);
}

function escapeHtml(value: string): string {
  return value
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

/* Adapted from emails/html/05-order-confirmation.html, which hardcodes a
   single sample line item for design review — this renders the real order's
   items instead of that placeholder. Keep the two in sync on brand changes. */
function renderHtml(input: OrderConfirmationInput): string {
  const rows = input.items
    .map((item) => {
      const detail = [item.colourName, item.size].filter(Boolean).join(" · ");
      return `
        <tr>
          <td style="padding:16px;border-bottom:1px solid #eee;" class="body-text">
            <div style="font-weight:bold;font-size:14px;">${escapeHtml(item.productName)}</div>
            <div class="small">${detail ? `${escapeHtml(detail)} · ` : ""}Qty: ${item.quantity}</div>
            <div style="font-weight:bold;margin-top:4px;">${money(item.unitPriceCents * item.quantity)}</div>
          </td>
        </tr>`;
    })
    .join("");

  return `<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<style>
body, table, td, a { -webkit-text-size-adjust: 100%; -ms-text-size-adjust: 100%; }
table, td { mso-table-lspace: 0pt; mso-table-rspace: 0pt; border-collapse: collapse; }
img { border: 0; height: auto; display: block; }
body { margin: 0 !important; padding: 0 !important; background-color: #0a0a0a; }
a { text-decoration: none; }
.display { font-family: Impact, Haettenschweiler, 'Arial Narrow Bold', 'Arial Black', Arial, sans-serif; font-weight: 900; letter-spacing: -0.03em; text-transform: uppercase; line-height: 0.9; }
.body-text { font-family: Arial, Helvetica, sans-serif; line-height: 1.5; color: #111; }
.small { font-family: Arial, Helvetica, sans-serif; font-size: 12px; color: #333; }
</style>
</head>
<body style="margin:0;padding:0;background:#0a0a0a;">
<div style="display:none;max-height:0;overflow:hidden;opacity:0;">You're locked in. Order confirmed.</div>
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" style="background:#0a0a0a;">
<tr><td align="center">
<table role="presentation" width="600" cellpadding="0" cellspacing="0" border="0" style="width:600px;max-width:600px;background:#F5F0E6;">
<tr>
<td style="background:#000;padding:18px 24px;">
<span class="display" style="font-size:28px;color:#fff;">shirtfaced</span>
<span style="display:inline-block;width:26px;height:26px;background:#C8FF1A;border-radius:50%;margin-left:6px;vertical-align:middle;text-align:center;line-height:26px;font-size:14px;">☺</span>
</td>
</tr>
<tr>
<td style="padding:36px 32px 24px;background:#F5F0E6;">
<div class="display" style="font-size:42px;color:#000;margin-bottom:6px;">
ORDER<br><span style="background:#C8FF1A;padding:0 6px;">CONFIRMED.</span>
</div>
<div class="body-text" style="font-size:16px;color:#333;margin:16px 0 28px;">You're locked in, ${escapeHtml(input.toName)}.</div>
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" style="border:2px solid #111;background:#fff;margin-bottom:24px;">
<tr>
<td style="padding:16px;border-bottom:1px solid #eee;" class="body-text">
<span style="font-size:13px;font-weight:bold;">ORDER #${escapeHtml(input.reference)}</span>
</td>
</tr>
${rows}
<tr>
<td style="padding:12px 16px;border-top:1px solid #eee;" class="body-text">
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0">
<tr><td style="font-size:13px;">Subtotal</td><td align="right" style="font-size:13px;">${money(input.subtotalCents)}</td></tr>
<tr><td style="font-size:13px;padding-top:4px;">Shipping</td><td align="right" style="font-size:13px;padding-top:4px;">${money(input.shippingCents)}</td></tr>
<tr><td style="font-size:15px;font-weight:bold;padding-top:8px;">Total</td><td align="right" style="font-size:15px;font-weight:bold;padding-top:8px;">${money(input.totalCents)}</td></tr>
</table>
</td>
</tr>
</table>
</td>
</tr>
<tr>
<td style="background:#000;padding:22px;text-align:center;">
<div style="font-family:Arial,sans-serif;font-size:13px;color:#C8FF1A;font-weight:bold;">SHIRTFACED.WTF</div>
<div class="display" style="font-size:11px;color:#C8FF1A;margin-top:12px;">GOOD MATES, GREAT TIMES, SHIRTFACED.</div>
</td>
</tr>
</table>
</td></tr>
</table>
</body>
</html>`;
}

function renderText(input: OrderConfirmationInput): string {
  const lines = input.items
    .map((item) => {
      const detail = [item.colourName, item.size].filter(Boolean).join(" ");
      return `${item.productName}${detail ? ` (${detail})` : ""} x${item.quantity} — ${money(item.unitPriceCents * item.quantity)}`;
    })
    .join("\n");

  return `SHIRTFACED

ORDER CONFIRMED.
You're locked in, ${input.toName}.

Order #${input.reference}

${lines}

Subtotal: ${money(input.subtotalCents)}
Shipping: ${money(input.shippingCents)}
Total: ${money(input.totalCents)}

---
GOOD MATES. GREAT TIMES. SHIRTFACED.
shirtfaced.wtf`;
}

/**
 * Fires when an order is marked paid — see markOrderPaid in store-queries.ts.
 * A no-op if RESEND_API_KEY/RESEND_FROM_EMAIL aren't set, the same "leave it
 * unset and get an honest absence rather than a crash" pattern Stripe already
 * uses elsewhere in this codebase.
 */
export async function sendOrderConfirmationEmail(input: OrderConfirmationInput): Promise<void> {
  const apiKey = process.env.RESEND_API_KEY;
  const from = process.env.RESEND_FROM_EMAIL;
  if (!apiKey || !from) return;

  const resend = new Resend(apiKey);
  await resend.emails.send({
    from,
    to: input.toEmail,
    subject: `Order confirmed — #${input.reference}`,
    html: renderHtml(input),
    text: renderText(input),
  });
}

export type ShippingConfirmationItem = {
  productName: string;
  colourName: string | null;
  size: string | null;
  quantity: number;
};

export type ShippingConfirmationInput = {
  toEmail: string;
  toName: string;
  reference: string;
  trackingNumber: string;
  carrier: string | null;
  items: ShippingConfirmationItem[];
};

/* Adapted from emails/html/06-shipping-confirmation.html — that template
   references a tracking URL and an estimated delivery date, neither of which
   exist here (no carrier API is integrated, just a tracking number staff
   type in by hand), so both are dropped rather than pointing at a link or
   estimate this app can't actually back up. */
function renderShippingHtml(input: ShippingConfirmationInput): string {
  const rows = input.items
    .map((item) => {
      const detail = [item.colourName, item.size].filter(Boolean).join(" · ");
      return `
        <tr>
          <td style="padding:16px;border-bottom:1px solid #eee;" class="body-text">
            <div style="font-weight:bold;font-size:14px;">${escapeHtml(item.productName)}</div>
            <div class="small">${detail ? `${escapeHtml(detail)} · ` : ""}Qty: ${item.quantity}</div>
          </td>
        </tr>`;
    })
    .join("");

  return `<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<style>
body, table, td, a { -webkit-text-size-adjust: 100%; -ms-text-size-adjust: 100%; }
table, td { mso-table-lspace: 0pt; mso-table-rspace: 0pt; border-collapse: collapse; }
img { border: 0; height: auto; display: block; }
body { margin: 0 !important; padding: 0 !important; background-color: #0a0a0a; }
a { text-decoration: none; }
.display { font-family: Impact, Haettenschweiler, 'Arial Narrow Bold', 'Arial Black', Arial, sans-serif; font-weight: 900; letter-spacing: -0.03em; text-transform: uppercase; line-height: 0.9; }
.body-text { font-family: Arial, Helvetica, sans-serif; line-height: 1.5; color: #111; }
.small { font-family: Arial, Helvetica, sans-serif; font-size: 12px; color: #333; }
</style>
</head>
<body style="margin:0;padding:0;background:#0a0a0a;">
<div style="display:none;max-height:0;overflow:hidden;opacity:0;">It's on the way. Let's go.</div>
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" style="background:#0a0a0a;">
<tr><td align="center">
<table role="presentation" width="600" cellpadding="0" cellspacing="0" border="0" style="width:600px;max-width:600px;background:#F5F0E6;">
<tr>
<td style="background:#000;padding:18px 24px;">
<span class="display" style="font-size:28px;color:#fff;">shirtfaced</span>
<span style="display:inline-block;width:26px;height:26px;background:#C8FF1A;border-radius:50%;margin-left:6px;vertical-align:middle;text-align:center;line-height:26px;font-size:14px;">☺</span>
</td>
</tr>
<tr>
<td style="padding:36px 32px 24px;background:#F5F0E6;">
<div class="display" style="font-size:42px;color:#000;margin-bottom:8px;">
IT'S ON<br>THE WAY.
</div>
<div class="body-text" style="font-size:16px;color:#333;margin-bottom:24px;">${escapeHtml(input.toName)}, your order's on its way.</div>
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" style="border:2px solid #111;background:#fff;margin-bottom:24px;">
<tr>
<td style="padding:16px;" class="body-text">
<div style="font-size:13px;margin-bottom:8px;"><strong>ORDER #${escapeHtml(input.reference)}</strong></div>
<div style="font-size:13px;margin-bottom:4px;">TRACKING</div>
<div style="font-size:14px;font-weight:bold;letter-spacing:0.5px;">${escapeHtml(input.trackingNumber)}</div>
${input.carrier ? `<div class="small" style="margin-top:8px;">${escapeHtml(input.carrier)}</div>` : ""}
</td>
</tr>
${rows}
</table>
</td>
</tr>
<tr>
<td style="background:#000;padding:22px;text-align:center;">
<div style="font-family:Arial,sans-serif;font-size:13px;color:#C8FF1A;font-weight:bold;">SHIRTFACED.WTF</div>
<div class="display" style="font-size:11px;color:#C8FF1A;margin-top:12px;">GOOD MATES, GREAT TIMES, SHIRTFACED.</div>
</td>
</tr>
</table>
</td></tr>
</table>
</body>
</html>`;
}

function renderShippingText(input: ShippingConfirmationInput): string {
  const lines = input.items
    .map((item) => {
      const detail = [item.colourName, item.size].filter(Boolean).join(" ");
      return `${item.productName}${detail ? ` (${detail})` : ""} x${item.quantity}`;
    })
    .join("\n");

  return `SHIRTFACED

IT'S ON THE WAY.
${input.toName}, your order's on its way.

Order #${input.reference}
Tracking: ${input.trackingNumber}${input.carrier ? `\nCarrier: ${input.carrier}` : ""}

${lines}

---
GOOD MATES. GREAT TIMES. SHIRTFACED.
shirtfaced.wtf`;
}

/**
 * Fires when staff record a tracking number — see setOrderTracking in
 * store-queries.ts. Same env-gated no-op as sendOrderConfirmationEmail.
 */
export async function sendShippingConfirmationEmail(input: ShippingConfirmationInput): Promise<void> {
  const apiKey = process.env.RESEND_API_KEY;
  const from = process.env.RESEND_FROM_EMAIL;
  if (!apiKey || !from) return;

  const resend = new Resend(apiKey);
  await resend.emails.send({
    from,
    to: input.toEmail,
    subject: `Your order is on the way — #${input.reference}`,
    html: renderShippingHtml(input),
    text: renderShippingText(input),
  });
}

export type AbandonedCartItem = {
  productName: string;
  colourName: string | null;
  size: string | null;
  quantity: number;
  unitPriceCents: number;
};

export type AbandonedCartInput = {
  toEmail: string;
  items: AbandonedCartItem[];
  cartUrl: string;
};

/* Adapted from emails/html/04-abandoned-cart.html, which shows a single
   sample item — this lists everything actually left in the order. Links to
   /cart rather than reconstructing anything server-side: the storefront
   cart lives in the browser's own localStorage and is only ever cleared on
   a successful payment (see cart-context.tsx), so anyone who abandoned
   checkout still has these exact items sitting there. */
function renderAbandonedCartHtml(input: AbandonedCartInput): string {
  const rows = input.items
    .map((item) => {
      const detail = [item.colourName, item.size].filter(Boolean).join(" · ");
      return `
        <tr>
          <td style="padding:14px;border-bottom:1px solid #eee;" class="body-text">
            <div style="font-weight:bold;font-size:15px;">${escapeHtml(item.productName)}</div>
            <div class="small" style="margin-top:4px;">${detail ? `${escapeHtml(detail)} · ` : ""}Qty: ${item.quantity}</div>
            <div style="font-size:15px;margin-top:6px;font-weight:bold;">${money(item.unitPriceCents * item.quantity)}</div>
          </td>
        </tr>`;
    })
    .join("");

  return `<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<style>
body, table, td, a { -webkit-text-size-adjust: 100%; -ms-text-size-adjust: 100%; }
table, td { mso-table-lspace: 0pt; mso-table-rspace: 0pt; border-collapse: collapse; }
img { border: 0; height: auto; display: block; }
body { margin: 0 !important; padding: 0 !important; background-color: #0a0a0a; }
a { text-decoration: none; }
.display { font-family: Impact, Haettenschweiler, 'Arial Narrow Bold', 'Arial Black', Arial, sans-serif; font-weight: 900; letter-spacing: -0.03em; text-transform: uppercase; line-height: 0.9; }
.body-text { font-family: Arial, Helvetica, sans-serif; line-height: 1.5; color: #111; }
.small { font-family: Arial, Helvetica, sans-serif; font-size: 12px; color: #333; }
</style>
</head>
<body style="margin:0;padding:0;background:#0a0a0a;">
<div style="display:none;max-height:0;overflow:hidden;opacity:0;">Your cart is waiting. Hesitation is the only thing that sells out.</div>
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" style="background:#0a0a0a;">
<tr><td align="center">
<table role="presentation" width="600" cellpadding="0" cellspacing="0" border="0" style="width:600px;max-width:600px;background:#F5F0E6;">
<tr>
<td style="background:#000;padding:18px 24px;">
<span class="display" style="font-size:28px;color:#fff;">shirtfaced</span>
<span style="display:inline-block;width:26px;height:26px;background:#C8FF1A;border-radius:50%;margin-left:6px;vertical-align:middle;text-align:center;line-height:26px;font-size:14px;">☺</span>
</td>
</tr>
<tr>
<td style="padding:40px 32px 28px;background:#F5F0E6;">
<div class="display" style="font-size:42px;color:#000;margin-bottom:8px;">
LEFT SOMETHING<br>BEHIND?
</div>
<div style="width:120px;height:6px;background:#C8FF1A;margin:10px 0 18px;"></div>
<div class="body-text" style="font-size:16px;color:#333;margin-bottom:28px;">Your cart is waiting.</div>
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" style="background:#fff;border:2px solid #111;margin-bottom:24px;">
${rows}
</table>
<table role="presentation" cellpadding="0" cellspacing="0" border="0" style="margin-bottom:20px;">
<tr>
<td style="background:#000;">
<a href="${escapeHtml(input.cartUrl)}" style="display:inline-block;padding:14px 28px;font-family:Impact,'Arial Black',Arial,sans-serif;font-size:15px;color:#C8FF1A;text-transform:uppercase;letter-spacing:1px;">RETURN TO CART →</a>
</td>
</tr>
</table>
<div style="background:#111;color:#C8FF1A;padding:12px 16px;display:inline-block;font-family:Arial,sans-serif;font-size:13px;font-weight:bold;">
HESITATION IS THE ONLY THING THAT SELLS OUT. ☺
</div>
</td>
</tr>
<tr>
<td style="background:#000;padding:22px;text-align:center;">
<div style="font-family:Arial,sans-serif;font-size:13px;color:#C8FF1A;font-weight:bold;">SHIRTFACED.WTF</div>
<div class="display" style="font-size:11px;color:#C8FF1A;margin-top:12px;">GOOD MATES, GREAT TIMES, SHIRTFACED.</div>
</td>
</tr>
</table>
</td></tr>
</table>
</body>
</html>`;
}

function renderAbandonedCartText(input: AbandonedCartInput): string {
  const lines = input.items
    .map((item) => {
      const detail = [item.colourName, item.size].filter(Boolean).join(" ");
      return `${item.productName}${detail ? ` (${detail})` : ""} x${item.quantity} — ${money(item.unitPriceCents * item.quantity)}`;
    })
    .join("\n");

  return `SHIRTFACED

LEFT SOMETHING BEHIND?
Your cart is waiting.

${lines}

RETURN TO CART → ${input.cartUrl}

Hesitation is the only thing that sells out.

---
GOOD MATES. GREAT TIMES. SHIRTFACED.
shirtfaced.wtf`;
}

/**
 * Fires from the notify-abandoned-orders script (see
 * admin/src/db/notify-abandoned-orders.ts) — a cron job on the box, not
 * anything triggered by a request. Same env-gated no-op as the other two
 * order emails.
 */
export async function sendAbandonedCartEmail(input: AbandonedCartInput): Promise<void> {
  const apiKey = process.env.RESEND_API_KEY;
  const from = process.env.RESEND_FROM_EMAIL;
  if (!apiKey || !from) return;

  const resend = new Resend(apiKey);
  await resend.emails.send({
    from,
    to: input.toEmail,
    subject: "Left something behind?",
    html: renderAbandonedCartHtml(input),
    text: renderAbandonedCartText(input),
  });
}
