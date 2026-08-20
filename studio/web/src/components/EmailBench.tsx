import { useEffect, useState } from "react";

import { Button, cx, Input, Select } from "./ui";

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

const cardClass = "rounded-[18px] border border-ink/10 bg-paper-2 p-5";

export function EmailBench(): React.JSX.Element {
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
        const firstTemplate = templateItems[0];
        if (firstTemplate) {
          setTemplateKey(firstTemplate.key);
        }
      })
      .catch((reason: unknown) => {
        setError(reason instanceof Error ? reason.message : "Unable to load Email Studio.");
      });
  }, []);

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
      <div className="mb-7">
        <h1 className="display m-0 text-[40px]">Email</h1>
        <p className="max-w-[720px] text-ink/70">
          Build and prove the email system before there is anything worth blasting at people. DNS,
          consent, templates and delivery all use the same production contracts.
        </p>
      </div>

      {error ? <div className="mb-4 text-coral">{error}</div> : null}

      <div className="grid grid-cols-[repeat(auto-fit,minmax(300px,1fr))] gap-4">
        <div className={cardClass}>
          <h2 className="mt-0">DNS readiness</h2>
          <p className="text-ink/70">
            {dnsPlan
              ? `${dnsPlan.status.toUpperCase()} — public DNS has not been changed.`
              : "Loading…"}
          </p>
          {dnsPlan ? (
            <>
              <p>
                <strong>Transactional:</strong> {dnsPlan.transactional_domain}
              </p>
              <p>
                <strong>Marketing:</strong> {dnsPlan.marketing_domain}
              </p>
              <p>
                <strong>Tracking:</strong> {dnsPlan.tracking_domain}
              </p>
              <div className="mt-4 grid gap-2">
                {Object.entries(dnsPlan.records).map(([key, value]) => (
                  <div key={key} className="flex justify-between gap-3">
                    <span>{key.replaceAll("_", " ")}</span>
                    <strong>{value.status}</strong>
                  </div>
                ))}
              </div>
            </>
          ) : null}
        </div>

        <div className={cardClass}>
          <h2 className="mt-0">Preview</h2>
          <div className="grid gap-3">
            <Select
              options={templates.map((item) => ({
                value: item.key,
                label: `${item.name} / ${item.purpose}`,
              }))}
              value={templateKey}
              onChange={(value) => {
                setTemplateKey(value);
              }}
            />
            <Input
              value={email}
              onChange={(event) => {
                setEmail(event.currentTarget.value);
              }}
              placeholder="Email"
            />
            <Input
              value={name}
              onChange={(event) => {
                setName(event.currentTarget.value);
              }}
              placeholder="Name"
            />
            <Button
              onClick={() => {
                void runPreview();
              }}
              isLoading={busy}
            >
              Generate preview
            </Button>
          </div>
        </div>
      </div>

      {message ? (
        <div className={cx(cardClass, "mt-4")}>
          <div className="flex flex-wrap justify-between gap-4">
            <div>
              <div className="text-[12px] font-bold uppercase">
                {message.purpose} / {message.state}
              </div>
              <h2 className="mb-1">{message.subject}</h2>
              <div className="text-ink/70">
                Eligibility: {message.eligible ? "yes" : "no"} — {message.eligibility_reason}
              </div>
            </div>
            <div className="flex flex-wrap items-start gap-2">
              {message.purpose === "marketing" ? (
                <Button
                  variant="secondary"
                  onClick={() => {
                    void setMarketingConsent(email, true).then(runPreview);
                  }}
                >
                  Grant test consent
                </Button>
              ) : null}
              <Button
                variant="secondary"
                isLoading={busy}
                onClick={() => {
                  setBusy(true);
                  void testSendEmail(message.id)
                    .then((result) => {
                      setMessage(result);
                    })
                    .catch((reason: unknown) => {
                      setError(reason instanceof Error ? reason.message : "Test send failed.");
                    })
                    .finally(() => {
                      setBusy(false);
                    });
                }}
              >
                Test delivery
              </Button>
            </div>
          </div>
          <iframe
            title="Email preview"
            srcDoc={message.html_body}
            className="mt-5 min-h-[520px] w-full border border-ink/10 bg-white"
          />
          {message.failure_reason ? <p className="text-coral">{message.failure_reason}</p> : null}
        </div>
      ) : null}
    </section>
  );
}
