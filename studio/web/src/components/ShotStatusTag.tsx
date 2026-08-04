/**
 * Status presentation for a shot.
 *
 * Colour alone must not carry the meaning, so every tag also states its status in
 * words.
 */

import { Tag, HIERARCHY, KIND, type TagKind } from "baseui/tag";

import type { ShotStatus } from "../api/client";

const LABELS: Record<ShotStatus, string> = {
  planned: "Planned",
  in_progress: "In progress",
  approved: "Approved",
  rejected: "Rejected",
  abandoned: "Abandoned",
};

const KINDS: Record<ShotStatus, TagKind> = {
  planned: KIND.neutral,
  in_progress: KIND.accent,
  approved: KIND.positive,
  rejected: KIND.negative,
  abandoned: KIND.warning,
};

export function statusLabel(status: ShotStatus): string {
  return LABELS[status];
}

export function ShotStatusTag({ status }: { status: ShotStatus }): React.JSX.Element {
  return (
    <Tag closeable={false} kind={KINDS[status]} hierarchy={HIERARCHY.secondary}>
      {LABELS[status]}
    </Tag>
  );
}
