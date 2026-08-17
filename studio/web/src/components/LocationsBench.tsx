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
import { useStyletron } from "baseui";
import { Button, KIND as BUTTON_KIND, SIZE } from "baseui/button";
import { Checkbox } from "baseui/checkbox";
import { Input } from "baseui/input";
import { Notification, KIND as NOTIFICATION_KIND } from "baseui/notification";
import { Select, type Value } from "baseui/select";
import { Tag, KIND as TAG_KIND } from "baseui/tag";
import { LabelSmall, ParagraphXSmall } from "baseui/typography";

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

export function LocationsBench(): React.JSX.Element {
  const [css, theme] = useStyletron();
  const [locations, setLocations] = useState<ScoutLocation[]>([]);
  const [roles, setRoles] = useState<string[]>([]);
  const [selected, setSelected] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [note, setNote] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);

  const [newName, setNewName] = useState("");
  const [childOf, setChildOf] = useState(false);
  const [plateRole, setPlateRole] = useState<Value>([]);
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
    const role = plateRole[0]?.id;
    if (!file || !location || typeof role !== "string") return;

    void act(async () => {
      const added = await addPlate(location.slug, file, {
        role,
        promote: promoteOnUpload,
      });
      if (plateInput.current) plateInput.current.value = "";
      if (added.is_base_master) return `Added and promoted: scenes here are built into it.`;
      return added.blocking.length > 0
        ? `Added as ${label(role)}. Not a base master: ${added.blocking.join("; ")}.`
        : `Added as ${label(role)}. It can be promoted whenever you want.`;
    });
  }, [act, location, plateRole, promoteOnUpload]);

  const card = css({
    border: `1px solid ${theme.colors.borderOpaque}`,
    borderRadius: "10px",
    padding: "10px",
    display: "flex",
    flexDirection: "column",
    gap: "8px",
    background: theme.colors.backgroundSecondary,
  });

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

      {error ? (
        <Notification
          kind={NOTIFICATION_KIND.negative}
          overrides={{ Body: { style: { width: "auto" } } }}
        >
          {error}
        </Notification>
      ) : null}
      {note ? (
        <Notification
          kind={NOTIFICATION_KIND.positive}
          overrides={{ Body: { style: { width: "auto" } } }}
        >
          {note}
        </Notification>
      ) : null}

      <div className={css({ display: "flex", gap: "6px", flexWrap: "wrap", margin: "12px 0" })}>
        {locations.map((one) => (
          <Button
            key={one.slug}
            size={SIZE.compact}
            kind={one.slug === selected ? BUTTON_KIND.primary : BUTTON_KIND.secondary}
            onClick={() => {
              setSelected(one.slug);
              setNote(null);
            }}
          >
            {one.parent_slug ? `↳ ${one.display_name}` : one.display_name}
            <span className={css({ opacity: 0.6, marginLeft: "6px" })}>
              {String(one.assets.length)}
            </span>
          </Button>
        ))}
      </div>

      <div
        className={css({
          display: "flex",
          gap: "8px",
          alignItems: "center",
          flexWrap: "wrap",
          marginBottom: "24px",
        })}
      >
        <Input
          value={newName}
          onChange={(event) => {
            setNewName(event.currentTarget.value);
          }}
          placeholder="Add a place — its name"
          overrides={{ Root: { style: { width: "300px" } } }}
        />
        <Checkbox
          checked={childOf}
          disabled={!location}
          onChange={(event) => {
            setChildOf(event.currentTarget.checked);
          }}
        >
          {location ? `Inside ${location.display_name}` : "Inside the selected place"}
        </Checkbox>
        <Button
          size={SIZE.compact}
          kind={BUTTON_KIND.secondary}
          disabled={busy || slugify(newName) === ""}
          onClick={onCreate}
        >
          Add place
        </Button>
      </div>

      {location ? (
        <>
          <SectionTitle>{`${location.display_name} — plates`}</SectionTitle>
          <div
            className={css({
              display: "grid",
              gridTemplateColumns: "repeat(auto-fill, minmax(240px, 1fr))",
              gap: "12px",
              marginBottom: "24px",
            })}
          >
            {location.assets.map((plate) => (
              <div key={plate.id} className={card}>
                <img
                  src={previewSource(plate.asset)}
                  alt={`${location.display_name}, ${label(plate.role)}`}
                  className={css({
                    width: "100%",
                    height: "150px",
                    objectFit: "contain",
                    background: theme.colors.backgroundTertiary,
                    borderRadius: "6px",
                  })}
                />
                <div className={css({ display: "flex", gap: "4px", flexWrap: "wrap" })}>
                  <Tag
                    closeable={false}
                    kind={plate.is_base_master ? TAG_KIND.accent : TAG_KIND.neutral}
                    overrides={{ Text: { style: { maxWidth: "none" } } }}
                  >
                    {label(plate.role)}
                  </Tag>
                  {plate.is_base_master ? (
                    <Tag closeable={false} kind={TAG_KIND.positive}>
                      base master
                    </Tag>
                  ) : null}
                  {plate.meets_wide_preference ? (
                    <Tag closeable={false} kind={TAG_KIND.neutral}>
                      2.39:1+
                    </Tag>
                  ) : null}
                </div>
                <ParagraphXSmall className={css({ margin: 0 })}>
                  {`${String(plate.asset.width)}×${String(plate.asset.height)} · ${plate.ratio.toFixed(2)}:1 · ${String(
                    plate.lateral_room_px,
                  )}px of lateral room`}
                </ParagraphXSmall>
                <LabelSmall
                  className={css({
                    fontFamily: "monospace",
                    fontSize: "11px",
                    color: theme.colors.contentTertiary,
                  })}
                >
                  {plate.asset.sha256.slice(0, 12)}
                </LabelSmall>
                {plate.blocking.length > 0 ? (
                  <ParagraphXSmall
                    className={css({ margin: 0, color: theme.colors.contentSecondary })}
                  >
                    {`Cannot be the base master: ${plate.blocking.join("; ")}.`}
                  </ParagraphXSmall>
                ) : plate.is_base_master ? null : (
                  <Button
                    size={SIZE.mini}
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
          <div
            className={css({
              display: "grid",
              gridTemplateColumns: "repeat(auto-fit, minmax(200px, 1fr))",
              gap: "10px",
              alignItems: "center",
            })}
          >
            <input ref={plateInput} type="file" accept="image/png,image/jpeg,image/webp" />
            <Select
              options={roles.map((role) => ({ id: role, label: label(role) }))}
              value={plateRole}
              onChange={(params) => {
                setPlateRole(params.value);
              }}
              placeholder="Class"
            />
            <Checkbox
              checked={promoteOnUpload}
              onChange={(event) => {
                setPromoteOnUpload(event.currentTarget.checked);
              }}
            >
              Make it the stage
            </Checkbox>
            <Button disabled={busy || plateRole.length === 0} onClick={onAddPlate}>
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
