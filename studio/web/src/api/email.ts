export interface EmailTemplate {
  key: string;
  name: string;
  purpose: "transactional" | "marketing";
  subject: string;
}

export interface EmailMessage {
  id: string;
  recipient_email: string;
  template_key: string;
  purpose: string;
  subject: string;
  html_body: string;
  text_body: string;
  state: string;
  eligible: boolean | null;
  eligibility_reason: string | null;
  adapter: string | null;
  failure_reason: string | null;
  external_message_id: string | null;
}

export interface DnsPlan {
  status: string;
  root_domain: string;
  transactional_domain: string;
  marketing_domain: string;
  tracking_domain: string;
  records: Record<string, { status: string; value?: string | null; host?: string }>;
  mailboxes: string[];
}

async function checked<T>(response: Response): Promise<T> {
  if (!response.ok) {
    const body = (await response.json().catch(() => null)) as { detail?: string } | null;
    throw new Error(body?.detail ?? `Request failed (${response.status})`);
  }
  return (await response.json()) as T;
}

export async function getEmailTemplates(): Promise<EmailTemplate[]> {
  return checked<EmailTemplate[]>(await fetch("/api/email/templates"));
}

export async function getEmailDnsPlan(): Promise<DnsPlan> {
  return checked<DnsPlan>(await fetch("/api/email/dns-plan"));
}

export async function previewEmail(input: {
  email: string;
  display_name: string;
  template_key: string;
}): Promise<EmailMessage> {
  return checked<EmailMessage>(
    await fetch("/api/email/preview", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(input),
    }),
  );
}

export async function setMarketingConsent(email: string, subscribed: boolean): Promise<void> {
  await checked(
    await fetch("/api/email/consent", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email, subscribed, source: "studio" }),
    }),
  );
}

export async function testSendEmail(messageId: string): Promise<EmailMessage> {
  return checked<EmailMessage>(
    await fetch(`/api/email/messages/${messageId}/test-send`, { method: "POST" }),
  );
}
