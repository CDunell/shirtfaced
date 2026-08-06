/**
 * Putting a design on a photograph.
 *
 * The photographs are made with blank garments, so the design goes on here. Where
 * it goes is dragged rather than detected: finding a garment in a dark, half-
 * occluded frame without a model is the fragile part, and a person does it in
 * seconds.
 *
 * Rendering is real, not a preview. It takes about a second and costs nothing, so
 * what is on screen after a drag is the actual output rather than an approximation
 * of it that might disagree.
 */

import { useCallback, useEffect, useRef, useState } from "react";
import { useStyletron } from "baseui";
import { Button, KIND as BUTTON_KIND, SIZE } from "baseui/button";
import { Card, StyledBody } from "baseui/card";
import { Notification, KIND as NOTIFICATION_KIND } from "baseui/notification";
import { Select, type Value } from "baseui/select";
import { Tag, KIND as TAG_KIND } from "baseui/tag";
import { HeadingSmall, LabelSmall, ParagraphXSmall } from "baseui/typography";

import {
  ApiError,
  fetchDesigns,
  fetchPhotos,
  fetchPlacement,
  printPhoto,
  savePlacement,
  uploadPhoto,
  type Corners,
  type Design,
  type Photo,
} from "../api/client";

/** Where a design starts before anybody has moved it: chest-high, middle of frame. */
const DEFAULT_CORNERS: Corners = [
  [0.38, 0.34],
  [0.62, 0.34],
  [0.62, 0.62],
  [0.38, 0.62],
];

/** One arrow-key press, as a fraction of the photograph. Small on purpose. */
const NUDGE = 0.002;

type Dragging = { corner: number } | { whole: true } | null;

function describe(cause: unknown): string {
  if (cause instanceof ApiError) return cause.message;
  return "Something went wrong.";
}

function moveAll(corners: Corners, dx: number, dy: number): Corners {
  return corners.map(([x, y]): [number, number] => [x + dx, y + dy]);
}

export function PrintBench(): React.JSX.Element {
  const [css, theme] = useStyletron();

  const [photos, setPhotos] = useState<Photo[]>([]);
  const [designs, setDesigns] = useState<Design[]>([]);
  const [photo, setPhoto] = useState<Photo | null>(null);
  const [design, setDesign] = useState<Value>([]);
  const [corners, setCorners] = useState<Corners>(DEFAULT_CORNERS);
  // Tagged with the photograph it belongs to, so switching photographs shows the
  // new one without an effect reaching in to clear anything.
  const [printed, setPrinted] = useState<{ photoId: string; url: string } | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const frame = useRef<HTMLDivElement>(null);
  const dragging = useRef<Dragging>(null);
  // Read by the handlers that need the placement as it stands right now. React may
  // call a state updater more than once, so doing the saving and rendering inside
  // one would do it twice.
  const latest = useRef<Corners>(DEFAULT_CORNERS);
  const designName = design[0]?.id ? String(design[0].id) : null;

  useEffect(() => {
    latest.current = corners;
  }, [corners]);

  const reload = useCallback(() => {
    fetchPhotos()
      .then(setPhotos)
      .catch((cause: unknown) => {
        setError(describe(cause));
      });
  }, []);

  useEffect(() => {
    reload();
    fetchDesigns()
      .then((found) => {
        setDesigns(found);
        const only = found[0];
        if (only) setDesign([{ id: only.name, label: only.name }]);
      })
      .catch((cause: unknown) => {
        setError(describe(cause));
      });
  }, [reload]);

  // A photograph brings its own placement, or the default if nobody has placed one.
  useEffect(() => {
    if (!photo) return undefined;
    const controller = new AbortController();
    fetchPlacement(photo.id, controller.signal)
      .then((placement) => {
        setCorners(placement ? placement.corners : DEFAULT_CORNERS);
        if (placement?.design) setDesign([{ id: placement.design, label: placement.design }]);
      })
      .catch((cause: unknown) => {
        if (!controller.signal.aborted) setError(describe(cause));
      });
    return () => {
      controller.abort();
    };
  }, [photo]);

  /** Save where it sits, then render. Called when a drag finishes, not during. */
  const settle = useCallback(
    (next: Corners) => {
      if (!photo) return;
      setBusy(true);
      setError(null);
      savePlacement(photo.id, { corners: next, design: designName })
        .then(() => (designName ? printPhoto(photo.id, designName) : null))
        .then((blob) => {
          if (!blob) return;
          setPrinted((previous) => {
            // The old object URL is never coming back; keeping it leaks the bitmap.
            if (previous) URL.revokeObjectURL(previous.url);
            return { photoId: photo.id, url: URL.createObjectURL(blob) };
          });
          setPhotos((existing) =>
            existing.map((item) => (item.id === photo.id ? { ...item, placed: true } : item)),
          );
        })
        .catch((cause: unknown) => {
          setError(describe(cause));
        })
        .finally(() => {
          setBusy(false);
        });
    },
    [photo, designName],
  );

  const pointerFraction = useCallback((event: React.PointerEvent): [number, number] => {
    const box = frame.current?.getBoundingClientRect();
    if (!box) return [0, 0];
    return [(event.clientX - box.left) / box.width, (event.clientY - box.top) / box.height];
  }, []);

  const last = useRef<[number, number]>([0, 0]);

  const onPointerDown = useCallback(
    (event: React.PointerEvent, target: Dragging) => {
      event.preventDefault();
      // Captured on the frame rather than the handle. A finger is wider than the
      // thing it is holding and leaves it immediately; capturing here means the
      // drag follows anyway.
      //
      // Capture is an improvement, not a requirement -- moves are tracked on the
      // frame either way -- so a browser that refuses it must not take the drag
      // down with it.
      try {
        frame.current?.setPointerCapture(event.pointerId);
      } catch {
        // Nothing to do: the drag works without it.
      }
      frame.current?.focus();
      dragging.current = target;
      last.current = pointerFraction(event);
    },
    [pointerFraction],
  );

  const onPointerMove = useCallback(
    (event: React.PointerEvent) => {
      const target = dragging.current;
      if (!target) return;
      const [x, y] = pointerFraction(event);

      setCorners((current) => {
        if ("whole" in target) {
          const [px, py] = last.current;
          return moveAll(current, x - px, y - py);
        }
        return current.map((point, index): [number, number] =>
          index === target.corner ? [x, y] : point,
        );
      });
      last.current = [x, y];
    },
    [pointerFraction],
  );

  const onPointerUp = useCallback(() => {
    if (!dragging.current) return;
    dragging.current = null;
    settle(latest.current);
  }, [settle]);

  // Arrow keys move the whole placement. A drag is quick; a pixel is not.
  const onKeyDown = useCallback(
    (event: React.KeyboardEvent) => {
      const moves: Record<string, [number, number]> = {
        ArrowLeft: [-NUDGE, 0],
        ArrowRight: [NUDGE, 0],
        ArrowUp: [0, -NUDGE],
        ArrowDown: [0, NUDGE],
      };
      const move = moves[event.key];
      if (!move) return;
      event.preventDefault();
      const next = moveAll(latest.current, move[0], move[1]);
      setCorners(next);
      settle(next);
    },
    [settle],
  );

  const onFile = useCallback(
    (event: React.ChangeEvent<HTMLInputElement>) => {
      const file = event.target.files?.[0];
      if (!file) return;
      setBusy(true);
      setError(null);
      uploadPhoto(file)
        .then((uploaded) => {
          setPhotos((existing) => [uploaded, ...existing]);
          setPhoto(uploaded);
        })
        .catch((cause: unknown) => {
          setError(describe(cause));
        })
        .finally(() => {
          setBusy(false);
          event.target.value = "";
        });
    },
    [],
  );

  const polygon = corners.map(([x, y]) => `${String(x * 100)},${String(y * 100)}`).join(" ");

  return (
    <div className={css({ maxWidth: "980px", margin: "0 auto" })}>
      <HeadingSmall marginTop={0}>Print</HeadingSmall>
      <ParagraphXSmall color={theme.colors.contentTertiary} marginTop={0}>
        Drag the corners onto the garment. Every render is real and costs nothing, so what you see
        is the output.
      </ParagraphXSmall>

      {error && (
        <Notification
          kind={NOTIFICATION_KIND.negative}
          overrides={{ Body: { style: { width: "auto" } } }}
        >
          {error}
        </Notification>
      )}

      <Card>
        <StyledBody>
          <div className={css({ display: "flex", gap: theme.sizing.scale600, flexWrap: "wrap" })}>
            <div className={css({ flex: "1 1 260px" })}>
              <LabelSmall marginBottom={theme.sizing.scale300}>Photograph</LabelSmall>
              <Select
                options={photos.map((item) => ({
                  id: item.id,
                  label: `${item.label}${item.placed ? "  (placed)" : ""}`,
                }))}
                value={photo ? [{ id: photo.id, label: photo.label }] : []}
                placeholder={photos.length ? "Choose a photograph" : "Nothing here yet — upload one"}
                clearable={false}
                onChange={({ value }) => {
                  const id = value[0]?.id ? String(value[0].id) : null;
                  setPhoto(photos.find((item) => item.id === id) ?? null);
                }}
              />
            </div>

            <div className={css({ flex: "1 1 200px" })}>
              <LabelSmall marginBottom={theme.sizing.scale300}>Design</LabelSmall>
              <Select
                options={designs.map((item) => ({ id: item.name, label: item.name }))}
                value={design}
                placeholder={designs.length ? "Choose a design" : "No artwork yet"}
                clearable={false}
                onChange={({ value }) => {
                  setDesign(value);
                }}
              />
            </div>

            <div className={css({ display: "flex", alignItems: "flex-end" })}>
              <Button
                kind={BUTTON_KIND.secondary}
                size={SIZE.compact}
                onClick={() => document.getElementById("upload-photo")?.click()}
                disabled={busy}
              >
                Upload a photo
              </Button>
              <input
                id="upload-photo"
                type="file"
                accept="image/png,image/jpeg,image/webp"
                onChange={onFile}
                className={css({ display: "none" })}
              />
            </div>
          </div>
        </StyledBody>
      </Card>

      {photo && (
        <Card overrides={{ Root: { style: { marginTop: theme.sizing.scale600 } } }}>
          <StyledBody>
            <div
              className={css({
                display: "flex",
                alignItems: "center",
                gap: theme.sizing.scale300,
                marginBottom: theme.sizing.scale400,
                flexWrap: "wrap",
              })}
            >
              <LabelSmall>{photo.label}</LabelSmall>
              <Tag closeable={false} kind={photo.uploaded ? TAG_KIND.accent : TAG_KIND.neutral}>
                {photo.uploaded ? "uploaded" : "generated"}
              </Tag>
              {photo.from_prompt && (
                // Where it came from, so a frame is never an anonymous file.
                <Tag closeable={false} kind={TAG_KIND.positive}>
                  {photo.from_prompt.shot_external_id}
                  {photo.from_prompt.variation === 1
                    ? ""
                    : ` variation ${String(photo.from_prompt.variation)}`}
                </Tag>
              )}
              {busy && <ParagraphXSmall margin={0}>Printing…</ParagraphXSmall>}
              {!designName && (
                <ParagraphXSmall margin={0} color={theme.colors.contentTertiary}>
                  No design chosen, so nothing is printed yet.
                </ParagraphXSmall>
              )}
            </div>

            {/* The photograph and the handles share one box, so a corner in
                fractions is a corner on screen at any size.

                Pointer moves are tracked on this box rather than on the handle:
                a finger leaves a small target immediately, and tracking the box
                means the drag survives that. */}
            <div
              ref={frame}
              tabIndex={0}
              onKeyDown={onKeyDown}
              onPointerMove={onPointerMove}
              onPointerUp={onPointerUp}
              onPointerCancel={onPointerUp}
              className={css({
                position: "relative",
                width: "100%",
                lineHeight: 0,
                // Without this a drag on a phone scrolls the page instead.
                touchAction: "none",
                outline: "none",
                borderRadius: theme.borders.radius300,
                overflow: "hidden",
              })}
            >
              <img
                src={printed?.photoId === photo.id ? printed.url : photo.url}
                alt={photo.label}
                draggable={false}
                className={css({ width: "100%", height: "auto", display: "block" })}
              />

              {/* Outline only. The viewBox is stretched to the photograph, which
                  is fine for a shape and wrong for anything that has to stay
                  round or stay big enough to hit. */}
              <svg
                viewBox="0 0 100 100"
                preserveAspectRatio="none"
                className={css({
                  position: "absolute",
                  inset: 0,
                  width: "100%",
                  height: "100%",
                })}
              >
                <polygon
                  points={polygon}
                  fill="rgba(198, 255, 51, 0.10)"
                  stroke="#c6ff33"
                  strokeWidth={0.35}
                  vectorEffect="non-scaling-stroke"
                  className={css({ cursor: "move", touchAction: "none" })}
                  onPointerDown={(event) => {
                    onPointerDown(event, { whole: true });
                  }}
                />
              </svg>

              {/* Handles are HTML, not SVG: in a stretched viewBox a circle comes
                  out an ellipse a few pixels across, which is unhittable with a
                  finger. Each is a 44px target with a small dot drawn inside. */}
              {corners.map(([x, y], index) => (
                <div
                  key={index}
                  role="slider"
                  tabIndex={-1}
                  aria-label={`Corner ${String(index + 1)}`}
                  aria-valuetext={`${String(Math.round(x * 100))}%, ${String(Math.round(y * 100))}%`}
                  onPointerDown={(event) => {
                    onPointerDown(event, { corner: index });
                  }}
                  className={css({
                    position: "absolute",
                    left: `${String(x * 100)}%`,
                    top: `${String(y * 100)}%`,
                    width: "44px",
                    height: "44px",
                    marginLeft: "-22px",
                    marginTop: "-22px",
                    display: "grid",
                    placeItems: "center",
                    cursor: "grab",
                    touchAction: "none",
                  })}
                >
                  <span
                    className={css({
                      width: "16px",
                      height: "16px",
                      borderRadius: "50%",
                      backgroundColor: "#c6ff33",
                      border: "2px solid #0d0d0d",
                      boxShadow: "0 1px 3px rgba(0, 0, 0, 0.5)",
                    })}
                  />
                </div>
              ))}
            </div>

            <div
              className={css({
                display: "flex",
                gap: theme.sizing.scale300,
                marginTop: theme.sizing.scale500,
                flexWrap: "wrap",
              })}
            >
              <Button
                size={SIZE.compact}
                kind={BUTTON_KIND.secondary}
                onClick={() => {
                  setCorners(DEFAULT_CORNERS);
                  settle(DEFAULT_CORNERS);
                }}
                disabled={busy}
              >
                Reset placement
              </Button>
              {printed?.photoId === photo.id && (
                <Button
                  size={SIZE.compact}
                  kind={BUTTON_KIND.secondary}
                  onClick={() => {
                    const link = document.createElement("a");
                    link.href = printed.url;
                    link.download = `${photo.label.replace(/\.[^.]+$/, "")}-printed.png`;
                    link.click();
                  }}
                >
                  Download
                </Button>
              )}
            </div>

            <ParagraphXSmall color={theme.colors.contentTertiary} marginBottom={0}>
              Click the photograph, then use the arrow keys to nudge it.
            </ParagraphXSmall>
          </StyledBody>
        </Card>
      )}
    </div>
  );
}
