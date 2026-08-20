/**
 * The location department: places, their plates, and which one is the stage.
 *
 * A plate that cannot be a base master says why on its own card rather than
 * failing when someone tries — the reasons are all things a scout can fix, and
 * finding out three of them one refusal at a time is a waste of a trip.
 *
 * The width note is information, not a verdict. A plate is refused only if a
 * 9:16 window does not fit in it at all; the ratio and the lateral room are
 * shown so the owner can judge whether there is room for the shots they want.
 */

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import {
  Button,
  Checkbox,
  Input,
  LabelSmall,
  Notification,
  ParagraphXSmall,
  Select,
  Tag,
} from "./ui";

import { PageTitle, SectionTitle } from "./chrome";
import { ApiError } from "../api/client";
import {
  addPlate,
  createLocation,
  fetchLocationRoles,
  fetchLocations,
  previewSource,
  promotePlate,
  type ScoutLocation,
} from "../api/production";

function label(role: string): string {
  return role.replace(/_/g, " ");
}

function slugify(name: string): string {
  return name
    .trim()
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-+|-+$/g, "");
}

const cardClass = "flex flex-col gap-2 rounded-[10px] border border-ink/10 bg-paper-2 p-2.5";

export function LocationsBench(): React.JSX.Element {
  const [locations, setLocations] = useState<ScoutLocation[]>([]);
  const [roles, setRoles] = useState<string[]>([]);
  const [selected, setSelected] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [note, setNote] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);

  const [newName, setNewName] = useState("");
  const [childOf, setChildOf] = useState(false);
  const [plateRole, setPlateRole] = useState<string>("");
  const [promoteOnUpload, setPromoteOnUpload] = useState(false);
  const plateInput = useRef<HTMLInputElement>(null);

  useEffect(() => {
    const controller = new AbortController();
    Promise.all([fetchLocations(controller.signal), fetchLocationRoles(controller.signal)])
      .then(([places, roleList]) => {
        setLocations(places);
        setRoles(roleList);
        setSelected((current) => current ?? places[0]?.slug ?? null);
        setLoading(false);
      })
      .catch((cause: unknown) => {
        if (controller.signal.aborted) return;
        setError(cause instanceof ApiError ? cause.message : "Locations are unavailable.");
        setLoading(false);
      });
    return () => {
      controller.abort();
    };
  }, []);

  const act = useCallback(async (work: () => Promise<string | null>) => {
    setBusy(true);
    setError(null);
    setNote(null);
    try {
      const message = await work();
      setLocations(await fetchLocations());
      if (message) setNote(message);
    } catch (cause) {
      setError(cause instanceof ApiError ? cause.message : "That did not go through.");
    } finally {
      setBusy(false);
    }
  }, []);

  const location = useMemo(
    () => locations.find((one) => one.slug === selected) ?? null,
    [locations, selected],
  );

  const onCreate = useCallback(() => {
    const displayName = newName.trim();
    const slug = slugify(displayName);
    if (!slug) return;

    void act(async () => {
      await createLocation({
        slug,
        display_name: displayName,
        parent_slug: childOf && location ? location.slug : null,
      });
      setNewName("");
      setSelected(slug);
      return childOf && location
        ? `${displayName} added inside ${location.display_name}.`
        : `${displayName} added.`;
    });
  }, [act, childOf, location, newName]);

  const onAddPlate = useCallback(() => {
    const file = plateInput.current?.files?.[0];
    if (!file || !location || !plateRole) return;

    void act(async () => {
      const added = await addPlate(location.slug, file, {
        role: plateRole,
        promote: promoteOnUpload,
      });
      if (plateInput.current) plateInput.current.value = "";
      if (added.is_base_master) return `Added and promoted: scenes here are built into it.`;
      return added.blocking.length > 0
        ? `Added as ${label(plateRole)}. Not a base master: ${added.blocking.join("; ")}.`
        : `Added as ${label(plateRole)}. It can be promoted whenever you want.`;
    });
  }, [act, location, plateRole, promoteOnUpload]);

  const total = locations.reduce((sum, one) => sum + one.assets.length, 0);

  return (
    <>
      <PageTitle
        meta={loading ? "Loading" : `${String(locations.length)} places · ${String(total)} plates`}
      >
        Locations
      </PageTitle>
      <ParagraphXSmall>
        Reusable places, their scouting plates, and the one plate per place that scenes are built
        into. A sub-location falls back to its parent&apos;s plate.
      </ParagraphXSmall>

      {error ? <Notification kind="negative">{error}</Notification> : null}
      {note ? <Notification kind="positive">{note}</Notification> : null}

      <div className="my-3 flex flex-wrap gap-1.5">
        {locations.map((one) => (
          <Button
            key={one.slug}
            size="compact"
            variant={one.slug === selected ? "primary" : "secondary"}
            onClick={() => {
              setSelected(one.slug);
              setNote(null);
            }}
          >
            {one.parent_slug ? `↳ ${one.display_name}` : one.display_name}
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
          placeholder="Add a place — its name"
          className="w-[300px]"
        />
        <Checkbox
          checked={childOf}
          onChange={(checked) => {
            if (!location) return;
            setChildOf(checked);
          }}
          {...(!location ? { className: "pointer-events-none opacity-40" } : {})}
        >
          {location ? `Inside ${location.display_name}` : "Inside the selected place"}
        </Checkbox>
        <Button
          size="compact"
          variant="secondary"
          disabled={busy || slugify(newName) === ""}
          onClick={onCreate}
        >
          Add place
        </Button>
      </div>

      {location ? (
        <>
          <SectionTitle>{`${location.display_name} — plates`}</SectionTitle>
          <div className="mb-6 grid grid-cols-[repeat(auto-fill,minmax(240px,1fr))] gap-3">
            {location.assets.map((plate) => (
              <div key={plate.id} className={cardClass}>
                <img
                  src={previewSource(plate.asset)}
                  alt={`${location.display_name}, ${label(plate.role)}`}
                  className="h-[150px] w-full rounded-[6px] bg-paper-2 object-contain"
                />
                <div className="flex flex-wrap gap-1">
                  <Tag kind={plate.is_base_master ? "accent" : "neutral"}>{label(plate.role)}</Tag>
                  {plate.is_base_master ? <Tag kind="positive">base master</Tag> : null}
                  {plate.meets_wide_preference ? <Tag kind="neutral">2.39:1+</Tag> : null}
                </div>
                <ParagraphXSmall>
                  {`${String(plate.asset.width)}×${String(plate.asset.height)} · ${plate.ratio.toFixed(2)}:1 · ${String(
                    plate.lateral_room_px,
                  )}px of lateral room`}
                </ParagraphXSmall>
                <LabelSmall className="font-mono text-[11px] text-ink/50">
                  {plate.asset.sha256.slice(0, 12)}
                </LabelSmall>
                {plate.blocking.length > 0 ? (
                  <ParagraphXSmall className="text-ink/70">
                    {`Cannot be the base master: ${plate.blocking.join("; ")}.`}
                  </ParagraphXSmall>
                ) : plate.is_base_master ? null : (
                  <Button
                    size="compact"
                    disabled={busy}
                    onClick={() =>
                      void act(async () => {
                        await promotePlate(plate.id, "Promoted from the Locations bench");
                        return `Scenes at ${location.display_name} are now built into that plate.`;
                      })
                    }
                  >
                    Make this the stage
                  </Button>
                )}
              </div>
            ))}
          </div>
          {location.assets.length === 0 ? (
            <ParagraphXSmall>No plates yet for this place.</ParagraphXSmall>
          ) : null}

          <SectionTitle>Add a plate</SectionTitle>
          <div className="grid grid-cols-[repeat(auto-fit,minmax(200px,1fr))] items-center gap-2.5">
            <input ref={plateInput} type="file" accept="image/png,image/jpeg,image/webp" />
            <Select
              options={roles.map((role) => ({ value: role, label: label(role) }))}
              value={plateRole}
              onChange={(value) => {
                setPlateRole(value);
              }}
              placeholder="Class"
            />
            <Checkbox
              checked={promoteOnUpload}
              onChange={(checked) => {
                setPromoteOnUpload(checked);
              }}
            >
              Make it the stage
            </Checkbox>
            <Button disabled={busy || plateRole === ""} onClick={onAddPlate}>
              Add plate
            </Button>
          </div>
          <ParagraphXSmall>
            Only an empty or participant-neutral plate can be the stage. A survey or a lighting
            reference is held and used, but not generated into.
          </ParagraphXSmall>
        </>
      ) : null}
    </>
  );
}
