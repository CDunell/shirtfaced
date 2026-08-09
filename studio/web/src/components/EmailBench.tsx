import { useEffect, useMemo, useState } from "react";
import { useStyletron } from "baseui";
import { Button } from "baseui/button";
import { Input } from "baseui/input";
import { Select } from "baseui/select";

import {
  getEmailDnsPlan,
  getEmailTemplates,
  previewEmail,
  setMarketingConsent,
  testSendEmail,
  type DnsPlan,
  type EmailMessage,
  type EmailTemplate,
} from "../api/email";

export function EmailBench(): React.JSX.Element {
  const [css, theme] = useStyletron();
  const [templates, setTemplates] = useState<EmailTemplate[]>([]);
  const [dnsPlan, setDnsPlan] = useState<DnsPlan | null>(null);
  const [templateKey, setTemplateKey] = useState("welcome");
  const [email, setEmail] = useState("preview@shirtfaced.wtf");
  const [name, setName] = useState("mate");
  const [message, setMessage] = useState<EmailMessage | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    void Promise.all([getEmailTemplates(), getEmailDnsPlan()])
      .then(([templateItems, plan]) => {
        setTemplates(templateItems);
        setDnsPlan(plan);
        if (templateItems.length > 0) setTemplateKey(templateItems[0].key);
      })
      .catch((reason: unknown) => {
        setError(reason instanceof Error ? reason.message : "Unable to load Email Studio.");
      });
  }, []);

  const selectedTemplate = useMemo(
    () => templates.find((item) => item.key === templateKey),
    [templateKey, templates],
  );

  const card = css({
    border: `1px solid ${theme.colors.borderOpaque}`,
    borderRadius: "18px",
    padding: "20px",
    backgroundColor: theme.colors.backgroundSecondary,
  });

  const runPreview = async (): Promise<void> => {
    setBusy(true);
    setError(null);
    try {
      setMessage(await previewEmail({ email, display_name: name, template_key: templateKey }));
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Preview failed.");
    } finally {
      setBusy(false);
    }
  };

  return (
    <section>
      <div className={css({ marginBottom: "28px" })}>
        <h1 className={`display ${css({ fontSize: "40px", margin: 0 })}`}>Email</h1>
        <p className={css({ color: theme.colors.contentSecondary, maxWidth: "720px" })}>
          Build and prove the email system before there is anything worth blasting at people. DNS,
          consent, templates and delivery all use the same production contracts.
        </p>
      </div>

      {error ? (
        <div className={css({ marginBottom: "16px", color: theme.colors.negative })}>{error}</div>
      ) : null}

      <div className={css({ display: "grid", gridTemplateColumns: "repeat(auto-fit,minmax(300px,1fr))", gap: "16px" })}>
        <div className={card}>
          <h2 className={css({ marginTop: 0 })}>DNS readiness</h2>
          <p className={css({ color: theme.colors.contentSecondary })}>
            {dnsPlan ? `${dnsPlan.status.toUpperCase()} — public DNS has not been changed.` : "Loading…"}
          </p>
          {dnsPlan ? (
            <>
              <p><strong>Transactional:</strong> {dnsPlan.transactional_domain}</p>
              <p><strong>Marketing:</strong> {dnsPlan.marketing_domain}</p>
              <p><strong>Tracking:</strong> {dnsPlan.tracking_domain}</p>
              <div className={css({ marginTop: "16px", display: "grid", gap: "8px" })}>
                {Object.entries(dnsPlan.records).map(([key, value]) => (
                  <div key={key} className={css({ display: "flex", justifyContent: "space-between", gap: "12px" })}>
                    <span>{key.replaceAll("_", " ")}</span>
                    <strong>{value.status}</strong>
                  </div>
                ))}
              </div>
            </>
          ) : null}
        </div>

        <div className={card}>
          <h2 className={css({ marginTop: 0 })}>Preview</h2>
          <div className={css({ display: "grid", gap: "12px" })}>
            <Select
              options={templates.map((item) => ({ id: item.key, label: `${item.name} / ${item.purpose}` }))}
              value={templateKey ? [{ id: templateKey, label: selectedTemplate?.name ?? templateKey }] : []}
              onChange={({ value }) => setTemplateKey(String(value[0]?.id ?? ""))}
              clearable={false}
            />
            <Input value={email} onChange={(event) => setEmail(event.currentTarget.value)} placeholder="Email" />
            <Input value={name} onChange={(event) => setName(event.currentTarget.value)} placeholder="Name" />
            <Button onClick={() => void runPreview()} isLoading={busy}>Generate preview</Button>
          </div>
        </div>
      </div>

      {message ? (
        <div className={`${card} ${css({ marginTop: "16px" })}`}>
          <div className={css({ display: "flex", justifyContent: "space-between", gap: "16px", flexWrap: "wrap" })}>
            <div>
              <div className={css({ textTransform: "uppercase", fontSize: "12px", fontWeight: 700 })}>
                {message.purpose} / {message.state}
              </div>
              <h2 className={css({ marginBottom: "4px" })}>{message.subject}</h2>
              <div className={css({ color: theme.colors.contentSecondary })}>
                Eligibility: {message.eligible ? "yes" : "no"} — {message.eligibility_reason}
              </div>
            </div>
            <div className={css({ display: "flex", gap: "8px", alignItems: "flex-start", flexWrap: "wrap" })}>
              {message.purpose === "marketing" ? (
                <Button
                  kind="secondary"
                  onClick={() => {
                    void setMarketingConsent(email, true).then(runPreview);
                  }}
                >
                  Grant test consent
                </Button>
              ) : null}
              <Button
                kind="secondary"
                onClick={() => {
                  setBusy(true);
                  void testSendEmail(message.id)
                    .then(setMessage)
                    .catch((reason: unknown) => setError(reason instanceof Error ? reason.message : "Test send failed."))
                    .finally(() => setBusy(false));
                }}
                isLoading={busy}
              >
                Test delivery
              </Button>
            </div>
          </div>
          <iframe
            title="Email preview"
            srcDoc={message.html_body}
            className={css({ width: "100%", minHeight: "520px", border: `1px solid ${theme.colors.borderOpaque}`, backgroundColor: "white", marginTop: "20px" })}
          />
          {message.failure_reason ? (
            <p className={css({ color: theme.colors.negative })}>{message.failure_reason}</p>
          ) : null}
        </div>
      ) : null}
    </section>
  );
}
