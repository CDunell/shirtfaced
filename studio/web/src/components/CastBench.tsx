/**
 * The cast library.
 *
 * What this replaces: a form with six file inputs and a button that said
 * "Install six". It could hold two photographs of three people, at two fixed
 * filenames, and there was nowhere for a third — which is the whole reason
 * VISUAL_ASSET_LIBRARY.md exists.
 *
 * Here a member's references are a strip that grows. Adding one is a role and
 * a file; the database gives it an identity, and the renderer can later lock
 * that exact asset by ID and SHA rather than by opening a path and hoping.
 *
 * Two things are shown that a filesystem could not say: whether an image is
 * approved, and whether its bytes are already held under another name. Both
 * are decisions, and decisions are what the fixed slots kept losing.
 */

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { Button, Checkbox, Input, LabelSmall, Notification, ParagraphXSmall, Select, Tag } from "./ui";

import { PageTitle, SectionTitle } from "./chrome";
import { ApiError } from "../api/client";
import {
  approveAsset,
  assetSource,
  createCastMember,
  deprecateAsset,
  detachCastAsset,
  fetchCast,
  fetchCastRoles,
  slugify,
  updateCastAsset,
  uploadCastAsset,
  type CastAsset,
  type CastMember,
} from "../api/cast";

/** Reads better than ``head_shoulders_neutral`` under a photograph. */
function roleLabel(role: string): string {
  return role.replace(/_/g, " ");
}

function bytes(size: number): string {
  return size < 1024 * 1024
    ? `${String(Math.round(size / 1024))} KB`
    : `${(size / 1024 / 1024).toFixed(1)} MB`;
}

const cardClass = "flex flex-col gap-2 rounded-[10px] border border-ink/10 bg-paper-2 p-2.5";

export function CastBench(): React.JSX.Element {
  const [members, setMembers] = useState<CastMember[]>([]);
  const [roles, setRoles] = useState<string[]>([]);
  const [selected, setSelected] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [note, setNote] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);

  const [newName, setNewName] = useState("");
  const [uploadRole, setUploadRole] = useState("");
  const [uploadPrimary, setUploadPrimary] = useState(false);
  const [uploadApprove, setUploadApprove] = useState(false);
  const fileInput = useRef<HTMLInputElement>(null);

  const reload = useCallback(async (signal?: AbortSignal) => {
    const data = await fetchCast(signal);
    setMembers(data);
    return data;
  }, []);

  useEffect(() => {
    const controller = new AbortController();
    Promise.all([fetchCast(controller.signal), fetchCastRoles(controller.signal)])
      .then(([data, roleList]) => {
        setMembers(data);
        setRoles(roleList);
        setSelected((current) => current ?? data[0]?.slug ?? null);
        setLoading(false);
      })
      .catch((cause: unknown) => {
        if (controller.signal.aborted) return;
        setError(cause instanceof ApiError ? cause.message : "The cast library is unavailable.");
        setLoading(false);
      });
    return () => {
      controller.abort();
    };
  }, []);

  const member = useMemo(
    () => members.find((candidate) => candidate.slug === selected) ?? null,
    [members, selected],
  );

  const act = useCallback(
    async (work: () => Promise<string | null>) => {
      setBusy(true);
      setError(null);
      setNote(null);
      try {
        const message = await work();
        await reload();
        if (message) setNote(message);
      } catch (cause) {
        setError(cause instanceof ApiError ? cause.message : "That did not go through.");
      } finally {
        setBusy(false);
      }
    },
    [reload],
  );

  const onCreate = useCallback(() => {
    const displayName = newName.trim();
    const slug = slugify(displayName);
    if (!slug) return;

    void act(async () => {
      await createCastMember(slug, displayName);
      setNewName("");
      setSelected(slug);
      return `${displayName} added. No references yet — upload one below.`;
    });
  }, [act, newName]);

  const onUpload = useCallback(() => {
    const file = fileInput.current?.files?.[0];
    if (!file || !member || !uploadRole) return;

    void act(async () => {
      const added: CastAsset = await uploadCastAsset(member.slug, file, {
        role: uploadRole,
        isPrimary: uploadPrimary,
        approve: uploadApprove,
      });
      if (fileInput.current) fileInput.current.value = "";
      return added.duplicate_of
        ? `Those exact bytes were already held. Filed as ${roleLabel(uploadRole)} rather than stored twice.`
        : `Added as ${roleLabel(uploadRole)}. ${uploadApprove ? "Approved." : "Pending approval."}`;
    });
  }, [act, member, uploadApprove, uploadPrimary, uploadRole]);

  const total = members.reduce((sum, one) => sum + one.assets.length, 0);

  return (
    <>
      <PageTitle
        meta={
          loading ? "Loading" : `${String(members.length)} members · ${String(total)} references`
        }
      >
        Cast
      </PageTitle>
      <ParagraphXSmall>
        Every reference is a row with an identity, a hash and an approval state. A member can have
        as many as the work needs.
      </ParagraphXSmall>

      {error ? <Notification kind="negative">{error}</Notification> : null}
      {note ? <Notification kind="positive">{note}</Notification> : null}

      <div className="mt-3 mb-[18px] flex flex-wrap gap-1.5">
        {members.map((one) => (
          <Button
            key={one.slug}
            size="compact"
            variant={one.slug === selected ? "primary" : "secondary"}
            onClick={() => {
              setSelected(one.slug);
              setNote(null);
            }}
          >
            {one.display_name}
            <span className="ml-1.5 opacity-60">{String(one.assets.length)}</span>
          </Button>
        ))}
      </div>

      <div className="mb-6 flex flex-wrap items-center gap-2">
        <Input
          value={newName}
          onChange={(event) => {
            setNewName(event.currentTarget.value);
          }}
          onKeyDown={(event) => {
            if (event.key === "Enter") onCreate();
          }}
          placeholder="Add a cast member — their name"
          className="w-[320px]"
        />
        <Button
          size="compact"
          variant="secondary"
          disabled={busy || slugify(newName) === ""}
          onClick={onCreate}
        >
          {newName.trim() ? `Add ${slugify(newName)}` : "Add member"}
        </Button>
      </div>

      {member ? (
        <>
          <SectionTitle>{`${member.display_name} — references`}</SectionTitle>
          <div className="mb-6 grid grid-cols-[repeat(auto-fill,minmax(220px,1fr))] gap-3">
            {member.assets.map((link) => (
              <div key={link.link_id} className={cardClass}>
                <img
                  src={assetSource(link.asset)}
                  alt={`${member.display_name}, ${roleLabel(link.role)}`}
                  className="h-[220px] w-full rounded-[6px] bg-paper-2 object-contain"
                />
                <div className="flex flex-wrap gap-1">
                  <Tag kind={link.is_primary ? "accent" : "neutral"}>{roleLabel(link.role)}</Tag>
                  <Tag
                    kind={
                      link.asset.status === "approved"
                        ? "positive"
                        : link.asset.status === "pending"
                          ? "warning"
                          : "negative"
                    }
                  >
                    {link.asset.status}
                  </Tag>
                  {link.is_primary ? <Tag kind="accent">primary</Tag> : null}
                </div>
                <LabelSmall className="font-mono text-[11px] text-ink/50">
                  {link.asset.sha256.slice(0, 16)}
                </LabelSmall>
                <ParagraphXSmall className="m-0">
                  {`${String(link.asset.width)}×${String(link.asset.height)} · ${bytes(
                    link.asset.byte_size,
                  )} · rights ${link.asset.rights_status}`}
                </ParagraphXSmall>
                <div className="flex flex-wrap gap-1.5">
                  {link.asset.status === "approved" ? (
                    <Button
                      size="compact"
                      variant="ghost"
                      disabled={busy}
                      onClick={() =>
                        void act(async () => {
                          await deprecateAsset(link.asset.id, "Deprecated from the cast library");
                          return "Deprecated. The asset and its history remain.";
                        })
                      }
                    >
                      Deprecate
                    </Button>
                  ) : (
                    <Button
                      size="compact"
                      disabled={busy}
                      onClick={() =>
                        void act(async () => {
                          await approveAsset(link.asset.id, "Approved from the cast library");
                          return "Approved.";
                        })
                      }
                    >
                      Approve
                    </Button>
                  )}
                  {link.is_primary ? null : (
                    <Button
                      size="compact"
                      variant="ghost"
                      disabled={busy}
                      onClick={() =>
                        void act(async () => {
                          await updateCastAsset(member.slug, link.link_id, { is_primary: true });
                          return `Primary ${roleLabel(link.role)} for ${member.display_name}.`;
                        })
                      }
                    >
                      Make primary
                    </Button>
                  )}
                  <Button
                    size="compact"
                    variant="ghost"
                    disabled={busy}
                    onClick={() =>
                      void act(async () => {
                        await detachCastAsset(member.slug, link.link_id);
                        return "Detached. The asset keeps its identity and its bytes.";
                      })
                    }
                  >
                    Detach
                  </Button>
                </div>
              </div>
            ))}
          </div>

          <SectionTitle>Add a reference</SectionTitle>
          <div className="grid grid-cols-[repeat(auto-fit,minmax(200px,1fr))] items-center gap-2.5">
            <input ref={fileInput} type="file" accept="image/png,image/jpeg,image/webp" />
            <Select
              options={roles.map((role) => ({ value: role, label: roleLabel(role) }))}
              value={uploadRole}
              onChange={setUploadRole}
              placeholder="Role"
            />
            <Checkbox checked={uploadPrimary} onChange={setUploadPrimary}>
              Primary for this role
            </Checkbox>
            <Checkbox checked={uploadApprove} onChange={setUploadApprove}>
              Approve on upload
            </Checkbox>
            <Button disabled={busy || !uploadRole} onClick={onUpload}>
              Add reference
            </Button>
          </div>
          <ParagraphXSmall>
            Roles are a vocabulary, not a limit. An image the list does not name is still stored.
          </ParagraphXSmall>
        </>
      ) : null}
    </>
  );
}
