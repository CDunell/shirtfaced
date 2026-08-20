/**
 * Service status panel.
 *
 * Reports the liveness of the Studio API. This is deliberately honest about what it
 * knows: `/health` proves the process is running, not that the world files load or
 * that PostgreSQL is reachable. `/ready` covers that, and arrives with a later phase.
 */

import { useCallback, useEffect, useState } from "react";
import { Button, Card, MonoLabelSmall, ParagraphSmall, Spinner, Tag } from "./ui";

import { ApiError, fetchHealth, type HealthResponse } from "../api/client";

type Status =
  | { state: "loading" }
  | { state: "live"; health: HealthResponse }
  | { state: "unreachable"; message: string };

export function ServiceStatus(): React.JSX.Element {
  const [status, setStatus] = useState<Status>({ state: "loading" });

  // Resolves the status without touching state synchronously, so it is safe to call
  // from an effect. The initial state is already "loading".
  const load = useCallback(async (signal?: AbortSignal): Promise<void> => {
    try {
      const health = await fetchHealth(signal);
      setStatus({ state: "live", health });
    } catch (error: unknown) {
      if (signal?.aborted) return;
      const message =
        error instanceof ApiError ? error.message : "The Studio service could not be reached.";
      setStatus({ state: "unreachable", message });
    }
  }, []);

  useEffect(() => {
    const controller = new AbortController();
    // set-state-in-effect traces into `load` and sees setStatus, but those calls
    // happen after an await, not synchronously during the effect. Fetching on mount
    // is the intended behaviour here. When the real API screens land, this belongs in
    // a data-fetching layer rather than a hand-rolled effect.
    // eslint-disable-next-line react-hooks/set-state-in-effect
    void load(controller.signal);
    return () => {
      controller.abort();
    };
  }, [load]);

  // Setting state from an event handler is fine, unlike doing so inside an effect.
  const recheck = useCallback(() => {
    setStatus({ state: "loading" });
    void load();
  }, [load]);

  return (
    <Card title="Studio service">
      <div className="mb-4 flex items-center gap-4">
        {status.state === "loading" && <Spinner />}

        {status.state === "live" && (
          <>
            <Tag kind="positive">Live</Tag>
            <MonoLabelSmall>version {status.health.version}</MonoLabelSmall>
          </>
        )}

        {status.state === "unreachable" && <Tag kind="negative">Unreachable</Tag>}
      </div>

      <ParagraphSmall>
        {status.state === "loading" && "Checking the Studio service…"}
        {status.state === "live" &&
          "The application process is running. This check does not yet confirm that " +
            "PostgreSQL is reachable or that the world files load."}
        {status.state === "unreachable" && status.message}
      </ParagraphSmall>

      <div className="mt-4">
        <Button size="compact" onClick={recheck} disabled={status.state === "loading"}>
          Check again
        </Button>
      </div>
    </Card>
  );
}
