import { describe, expect, it, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import { AuditLogFilters } from "./AuditLogFilters";
import { NO_FILTER, type AuditFilters } from "@/lib/audit-filters";

vi.mock("@/lib/api/queries", () => ({
  useTeammates: () => ({
    teammates: [
      { id: 1, display_name: "Lin Chen" },
      { id: 2, display_name: "Nino Garo" },
    ],
  }),
}));

function bar(over: Partial<AuditFilters> = {}) {
  const onChange = vi.fn();
  const onClear = vi.fn();
  render(
    <AuditLogFilters
      filters={{ ...NO_FILTER, ...over }}
      onChange={onChange}
      onClear={onClear}
    />,
  );
  return { onChange, onClear };
}

describe("AuditLogFilters", () => {
  it("offers the gestures under the family they belong to", async () => {
    bar();

    await userEvent.click(screen.getByRole("button", { name: /Geste/ }));

    // The family is a heading, said once, above the gestures it holds.
    expect(screen.getByText("Projets")).toBeInTheDocument();
    expect(screen.getByText("Clés d'API")).toBeInTheDocument();
    expect(screen.getByText("Révocation")).toBeInTheDocument();
  });

  it("keeps the gesture that was ticked", async () => {
    const { onChange } = bar();

    await userEvent.click(screen.getByRole("button", { name: /Geste/ }));
    // « Suppression » is offered under three families; the one under
    // « Projets » is what a reader after a deleted mission clicks.
    await userEvent.click(
      screen.getByRole("button", { name: "Suppression", pressed: false }),
    );

    expect(onChange).toHaveBeenCalledWith({ actions: ["project.delete"] });
  });

  /**
   * The register answers one actor. Ticking a second would silently drop the
   * first, so the last click is what the bar keeps — and shows.
   */
  it("keeps one author at a time", async () => {
    const { onChange } = bar({ actorIds: ["1"] });

    await userEvent.click(screen.getByRole("button", { name: /Auteur/ }));
    await userEvent.click(screen.getByText("Nino Garo"));

    expect(onChange).toHaveBeenCalledWith({ actorIds: ["2"] });
  });

  it("looks a colleague up rather than scrolling to them", async () => {
    const { onChange } = bar();

    await userEvent.click(screen.getByRole("button", { name: /Auteur/ }));
    await userEvent.type(screen.getByLabelText("Rechercher un collaborateur"), "nino");
    await userEvent.click(screen.getByRole("button", { name: "Nino Garo" }));

    expect(screen.queryByRole("button", { name: "Lin Chen" })).toBeNull();
    expect(onChange).toHaveBeenCalledWith({ actorIds: ["2"] });
  });

  /** The gestures are grouped and few enough to read: a field there is furniture. */
  it("offers no search on the gestures", async () => {
    bar();

    await userEvent.click(screen.getByRole("button", { name: /Geste/ }));

    expect(screen.queryByRole("searchbox")).toBeNull();
  });

  it("asks for a period in days", async () => {
    const { onChange } = bar();

    const from = screen.getByLabelText("Du");
    await userEvent.type(from, "2026-09-01");

    expect(onChange).toHaveBeenCalled();
    expect(from).toHaveAttribute("type", "date");
  });

  /** One end of the period can never be set past the other. */
  it("keeps the two ends of the period in order", () => {
    bar({ fromDay: "2026-09-01", toDay: "2026-09-30" });

    expect(screen.getByLabelText("Du")).toHaveAttribute("max", "2026-09-30");
    expect(screen.getByLabelText("au")).toHaveAttribute("min", "2026-09-01");
  });

  /** Offering to clear what is already empty sends one looking for a filter. */
  it("offers clearing only once something is filtered", () => {
    const { onClear } = bar();
    expect(screen.queryByRole("button", { name: "Effacer" })).toBeNull();
    expect(onClear).not.toHaveBeenCalled();
  });

  it("offers clearing as soon as a criterion is set", async () => {
    const { onClear } = bar({ actions: ["project.delete"] });

    await userEvent.click(screen.getByRole("button", { name: "Effacer" }));

    expect(onClear).toHaveBeenCalledTimes(1);
  });
});
