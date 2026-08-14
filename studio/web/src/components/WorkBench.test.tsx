/**
 * Work is the plan's governing rule made literal, so these test the rule.
 *
 * "At every point there is exactly one obvious next action, and following the
 * chain requires no knowledge of which screen owns what." A row that shows a
 * status instead of an instruction, or a button that does not go anywhere,
 * fails that regardless of what it renders.
 */

import userEvent from "@testing-library/user-event";
import { screen, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { WorkBench } from "./WorkBench";
import { renderWithBase } from "../test/render";
import { stubApi, workItem } from "../test/stubs";

afterEach(() => {
  vi.unstubAllGlobals();
});

const noop = (): void => undefined;

describe("WorkBench", () => {
  it("leads with one thing to do, not a count of things to do", async () => {
    stubApi({ work: [workItem()] });

    renderWithBase(<WorkBench onOpen={noop} />);

    expect(await screen.findByText("Start here")).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "#001 ABSOLUTE WEAPON" })).toBeInTheDocument();
    expect(screen.getAllByText(/Passed at 80\/100 with no failed gates/).length).toBeGreaterThan(0);
  });

  it("labels the action with a verb rather than a state", async () => {
    // "Judge it" is a thing to do. "Awaiting decision" is a thing to be.
    stubApi({ work: [workItem()] });

    renderWithBase(<WorkBench onOpen={noop} />);

    await waitFor(() => {
      expect(screen.getAllByRole("button", { name: "Judge it" }).length).toBeGreaterThan(0);
    });
    expect(screen.queryByRole("button", { name: /awaiting/i })).not.toBeInTheDocument();
  });

  it("hands the row over rather than editing it here", async () => {
    const opened: string[] = [];
    stubApi({ work: [workItem()] });

    renderWithBase(
      <WorkBench
        onOpen={(item) => {
          opened.push(`${item.concept_id}:${String(item.attempt_id)}`);
        }}
      />,
    );

    await waitFor(() => {
      expect(screen.getAllByRole("button", { name: "Judge it" }).length).toBeGreaterThan(0);
    });
    await userEvent.click(screen.getAllByRole("button", { name: "Judge it" })[0]!);

    expect(opened).toEqual(["concept-1:attempt-1"]);
  });

  it("keeps the server's order rather than re-sorting in the browser", async () => {
    // The queue's order is the product. Re-deriving it here would be a second
    // opinion about which is most blocked.
    stubApi({
      work: [
        workItem({ concept_id: "c1", external_number: 9, title: "FIRST" }),
        workItem({
          concept_id: "c2",
          external_number: 2,
          title: "SECOND",
          stage: "needs_artwork",
          attempt_state: "planned",
          percentage: null,
          next_action: "Copy the brief and bring the artwork back to the drop zone below.",
        }),
      ],
    });

    renderWithBase(<WorkBench onOpen={noop} />);

    await waitFor(() => {
      expect(screen.getAllByTestId("work-row")).toHaveLength(2);
    });
    const rows = screen.getAllByTestId("work-row");
    expect(rows[0]).toHaveTextContent("FIRST");
    expect(rows[1]).toHaveTextContent("SECOND");
  });

  it("every row states its next action", async () => {
    stubApi({
      work: [
        workItem({ concept_id: "c1" }),
        workItem({
          concept_id: "c2",
          external_number: 4,
          stage: "unstarted",
          attempt_id: null,
          attempt_number: null,
          attempt_state: null,
          has_artwork: false,
          percentage: null,
          next_action: "Nothing has been made for this yet. Open it and start an attempt.",
        }),
      ],
    });

    renderWithBase(<WorkBench onOpen={noop} />);

    await waitFor(() => {
      expect(screen.getAllByTestId("work-row")).toHaveLength(2);
    });
    for (const row of screen.getAllByTestId("work-row")) {
      expect(row.textContent ?? "").toMatch(/\w+\./);
    }
  });

  it("says so plainly when there is nothing to do", async () => {
    stubApi({ work: [] });

    renderWithBase(<WorkBench onOpen={noop} />);

    expect(await screen.findByText(/Nothing is outstanding/)).toBeInTheDocument();
    expect(screen.queryByText("Start here")).not.toBeInTheDocument();
  });

  it("keeps settled work out of the way until asked", async () => {
    const spy = stubApi({ work: [workItem()] });

    renderWithBase(<WorkBench onOpen={noop} />);

    await waitFor(() => {
      expect(screen.getByRole("button", { name: "Show settled" })).toBeInTheDocument();
    });
    await userEvent.click(screen.getByRole("button", { name: "Show settled" }));

    await waitFor(() => {
      expect(spy.mock.calls.some(([url]) => String(url).includes("include_settled=true"))).toBe(
        true,
      );
    });
  });
});
