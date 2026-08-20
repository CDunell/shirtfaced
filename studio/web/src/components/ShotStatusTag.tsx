/**
 * Status presentation for a shot.
 *
 * Colour alone must not carry the meaning, so every tag also states its status in
 * words.
 */

import { Tag, type TagKind } from "./ui";

import type { ShotStatus } from "../api/client";

const LABELS: Record<ShotStatus, string> = {
  planned: "Planned",
  in_progress: "In progress",
  approved: "Approved",
  rejected: "Rejected",
  abandoned: "Abandoned",
};

const KINDS: Record<ShotStatus, TagKind> = {
  planned: "neutral",
  in_progress: "accent",
  approved: "positive",
  rejected: "negative",
  abandoned: "warning",
};

export function statusLabel(status: ShotStatus): string {
  return LABELS[status];
}

export function ShotStatusTag({ status }: { status: ShotStatus }): React.JSX.Element {
  return <Tag kind={KINDS[status]}>{LABELS[status]}</Tag>;
}
