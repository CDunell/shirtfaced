/**
 * Read-only world page.
 *
 * Shows the loaded canon version, how the shotlist breaks down, which shot comes next
 * and the full backlog. Nothing here changes state: Continue World, approval and
 * canon proposals arrive with the phases that implement them.
 */

import { useCallback, useEffect, useState } from "react";
import { useStyletron } from "baseui";
import { Card, StyledBody } from "baseui/card";
import { Notification, KIND as NOTIFICATION_KIND } from "baseui/notification";
import { Spinner } from "baseui/spinner";
import { Table } from "baseui/table-semantic";
import { Tag, HIERARCHY, KIND as TAG_KIND } from "baseui/tag";
import { HeadingSmall, LabelSmall, MonoLabelXSmall, ParagraphSmall } from "baseui/typography";

import { ApiError, fetchWorld, fetchWorlds, type Shot, type WorldDetail } from "../api/client";
import { GenerationPanel } from "./GenerationPanel";
import { SelectionPanel } from "./SelectionPanel";
import { ShotStatusTag, statusLabel } from "./ShotStatusTag";

type State =
  | { kind: "loading" }
  | { kind: "empty" }
  | { kind: "loaded"; world: WorldDetail }
  | { kind: "failed"; message: string };

const EM_DASH = "—";

function DocumentHash({
  label,
  digest,
}: {
  label: string;
  digest: string | null;
}): React.JSX.Element {
  const [css, theme] = useStyletron();

  return (
    <div className={css({ display: "flex", gap: theme.sizing.scale400, alignItems: "baseline" })}>
      <LabelSmall>{label}</LabelSmall>
      <MonoLabelXSmall color={theme.colors.contentSecondary}>
        {digest ? `${digest.slice(0, 12)}…` : "not recorded"}
      </MonoLabelXSmall>
    </div>
  );
}

function CountsRow({ world }: { world: WorldDetail }): React.JSX.Element {
  const [css, theme] = useStyletron();
  const { counts } = world;

  const entries: [string, number][] = [
    ["Planned", counts.planned],
    ["In progress", counts.in_progress],
    ["Approved", counts.approved],
    ["Rejected", counts.rejected],
    ["Abandoned", counts.abandoned],
  ];

  return (
    <div className={css({ display: "flex", flexWrap: "wrap", gap: theme.sizing.scale300 })}>
      <Tag closeable={false} kind={TAG_KIND.primary} hierarchy={HIERARCHY.primary}>
        {`${String(counts.total)} shots`}
      </Tag>
      {entries
        .filter(([, total]) => total > 0)
        .map(([label, total]) => (
          <Tag
            key={label}
            closeable={false}
            kind={TAG_KIND.neutral}
            hierarchy={HIERARCHY.secondary}
          >
            {`${label}: ${String(total)}`}
          </Tag>
        ))}
    </div>
  );
}

function Shotlist({ shots }: { shots: Shot[] }): React.JSX.Element {
  const rows = shots.map((shot) => [
    shot.external_id,
    shot.title,
    shot.hero_product ?? EM_DASH,
    shot.camera_position ?? EM_DASH,
    <ShotStatusTag key={shot.id} status={shot.status} />,
  ]);

  return (
    <Table
      columns={["ID", "Scene", "Hero product", "Camera", "Status"]}
      data={rows}
      emptyMessage="This world has no shots. Import it to load SHOTLIST.md."
    />
  );
}

export function WorldPage(): React.JSX.Element {
  const [css, theme] = useStyletron();
  const [state, setState] = useState<State>({ kind: "loading" });

  const load = useCallback(async (signal?: AbortSignal): Promise<void> => {
    try {
      const worlds = await fetchWorlds(signal);
      const first = worlds[0];
      if (!first) {
        setState({ kind: "empty" });
        return;
      }
      setState({ kind: "loaded", world: await fetchWorld(first.slug, signal) });
    } catch (error: unknown) {
      if (signal?.aborted) return;
      setState({
        kind: "failed",
        message: error instanceof ApiError ? error.message : "The world could not be loaded.",
      });
    }
  }, []);

  useEffect(() => {
    const controller = new AbortController();
    // Fetching on mount: setState happens after an await, not during the effect.
    // eslint-disable-next-line react-hooks/set-state-in-effect
    void load(controller.signal);
    return () => {
      controller.abort();
    };
  }, [load]);

  if (state.kind === "loading") {
    return <Spinner $size={theme.sizing.scale900} />;
  }

  if (state.kind === "failed") {
    return <Notification kind={NOTIFICATION_KIND.negative}>{state.message}</Notification>;
  }

  if (state.kind === "empty") {
    return (
      <Notification kind={NOTIFICATION_KIND.warning}>
        No worlds have been imported yet. Run: python -m app.cli import-world world-01
      </Notification>
    );
  }

  const { world } = state;

  return (
    <>
      <div
        className={css({
          display: "flex",
          alignItems: "center",
          gap: theme.sizing.scale500,
          flexWrap: "wrap",
        })}
      >
        <HeadingSmall marginTop={0} marginBottom={0}>
          {world.name}
        </HeadingSmall>
        <Tag closeable={false} kind={TAG_KIND.positive} hierarchy={HIERARCHY.secondary}>
          {world.status === "active" ? "Active" : "Archived"}
        </Tag>
      </div>

      <div className={css({ marginTop: theme.sizing.scale600 })}>
        <CountsRow world={world} />
      </div>

      <div
        className={css({
          display: "grid",
          gap: theme.sizing.scale700,
          gridTemplateColumns: "repeat(auto-fit, minmax(320px, 1fr))",
          marginTop: theme.sizing.scale700,
        })}
      >
        <SelectionPanel slug={world.slug} />

        <GenerationPanel slug={world.slug} onGenerated={() => void load()} />

        <Card title="Loaded canon">
          <StyledBody>
            <div className={css({ display: "grid", gap: theme.sizing.scale200 })}>
              <DocumentHash label="WORLD.md" digest={world.world_document_hash} />
              <DocumentHash label="CONTINUITY.md" digest={world.continuity_document_hash} />
              <DocumentHash label="SHOTLIST.md" digest={world.shotlist_document_hash} />
            </div>
            <ParagraphSmall marginBottom={0} color={theme.colors.contentSecondary}>
              These hashes identify the exact document versions this state was built from. Editing a
              file and re-importing changes them.
            </ParagraphSmall>
          </StyledBody>
        </Card>
      </div>

      <div className={css({ marginTop: theme.sizing.scale800 })}>
        <HeadingSmall marginBottom={theme.sizing.scale500}>Shotlist</HeadingSmall>
        <Shotlist shots={world.shots} />
        <ParagraphSmall color={theme.colors.contentSecondary}>
          Read-only. Statuses shown are{" "}
          {[...new Set(world.shots.map((shot) => statusLabel(shot.status)))].join(", ")}.
        </ParagraphSmall>
      </div>
    </>
  );
}
