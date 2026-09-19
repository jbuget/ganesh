import { describe, expect, it, vi } from "vitest";
import { fireEvent, render, screen } from "@testing-library/react";

import { MissionFilters } from "./MissionFilters";
import { NO_FILTER, type MissionFilters as Criteria } from "@/lib/mission-filters";

vi.mock("@/lib/api/queries", () => ({
  useTeammates: () => ({
    teammates: [{ id: 3, display_name: "Nino Bosc", initials: "NB" }],
  }),
}));

const bar = (over: Partial<Criteria> = {}, props: Record<string, unknown> = {}) => {
  const filters = { ...NO_FILTER, ...over };
  const onChange = vi.fn();
  const onClear = vi.fn();
  render(
    <MissionFilters
      filters={filters}
      hasFilter={
        filters.name !== "" ||
        filters.phases.length > 0 ||
        filters.categories.length > 0 ||
        filters.priorities.length > 0 ||
        filters.contributors.length > 0 ||
        filters.types.length > 0 ||
        filters.states.length > 0
      }
      onChange={onChange}
      onClear={onClear}
      visible={3}
      total={12}
      {...props}
    />,
  );
  return { onChange, onClear };
};

describe("MissionFilters", () => {
  /**
   * The kanban offers nothing there, the reference list puts the choice of
   * columns in it: the bar holds the place without knowing what goes in it.
   */
  it("hangs what the screen gives it at the far end of the bar", () => {
    bar({}, { trailing: <button type="button">Colonnes</button> });

    expect(screen.getByRole("button", { name: "Colonnes" })).toBeInTheDocument();
  });

  it("offers every criterion the two mission screens share", () => {
    bar();

    expect(screen.getByLabelText("Rechercher une mission")).toBeInTheDocument();
    [
      "Phase",
      "Catégorie",
      "Département",
      "Priorité",
      "Intervenant",
      "Type",
      "Publication",
      "État",
    ].forEach((criterion) => {
      expect(
        screen.getByRole("button", { name: new RegExp(criterion) }),
      ).toBeInTheDocument();
    });
  });

  it("reports the search typed", () => {
    const { onChange } = bar();

    fireEvent.change(screen.getByLabelText("Rechercher une mission"), {
      target: { value: "portail" },
    });

    expect(onChange).toHaveBeenCalledWith({ name: "portail" });
  });

  it("reports a ticked phase", () => {
    const { onChange } = bar();

    fireEvent.click(screen.getByRole("button", { name: /Phase/ }));
    fireEvent.click(screen.getByRole("button", { name: "Réalisation" }));

    expect(onChange).toHaveBeenCalledWith({ phases: ["development"] });
  });

  it("reports a ticked contributor, by their id", () => {
    const { onChange } = bar();

    fireEvent.click(screen.getByRole("button", { name: /Intervenant/ }));
    fireEvent.click(screen.getByRole("button", { name: /Nino Bosc/ }));

    expect(onChange).toHaveBeenCalledWith({ contributors: [3] });
  });

  it("tells projects from sub-projects", () => {
    const { onChange } = bar();

    fireEvent.click(screen.getByRole("button", { name: /Type/ }));
    fireEvent.click(screen.getByRole("button", { name: "Sous-projets" }));

    expect(onChange).toHaveBeenCalledWith({ types: ["work_package"] });
  });

  it("reports a ticked priority", () => {
    const { onChange } = bar();

    fireEvent.click(screen.getByRole("button", { name: /Priorité/ }));
    fireEvent.click(screen.getByRole("button", { name: "Critique" }));

    expect(onChange).toHaveBeenCalledWith({ priorities: ["critical"] });
  });

  it("reports a ticked department", () => {
    const { onChange } = bar();

    fireEvent.click(screen.getByRole("button", { name: /Département/ }));
    fireEvent.click(screen.getByRole("button", { name: "Copropriété" }));

    expect(onChange).toHaveBeenCalledWith({ departments: ["condominium"] });
  });

  /** Tending the catalogue: which missions still have no service sheet. */
  it("offers to look at the missions with no service sheet", () => {
    const { onChange } = bar();

    fireEvent.click(screen.getByRole("button", { name: /Publication/ }));
    fireEvent.click(screen.getByRole("button", { name: "Non publiées" }));

    expect(onChange).toHaveBeenCalledWith({ publications: ["unpublished"] });
  });

  it("offers to look at archived missions", () => {
    const { onChange } = bar();

    fireEvent.click(screen.getByRole("button", { name: /État/ }));
    fireEvent.click(screen.getByRole("button", { name: "Archivées" }));

    expect(onChange).toHaveBeenCalledWith({ states: ["archived"] });
  });

  it("offers to clear only when there is something to clear", () => {
    bar();

    expect(screen.queryByRole("button", { name: "Effacer" })).toBeNull();
  });

  it("clears every criterion in one click", () => {
    const { onClear } = bar({ name: "portail" });

    fireEvent.click(screen.getByRole("button", { name: "Effacer" }));

    expect(onClear).toHaveBeenCalledTimes(1);
  });

  it("says what is seen against what the screen carries", () => {
    bar({ phases: ["scoping"] });

    expect(screen.getByRole("status")).toHaveTextContent("3 missions sur 12");
  });

  it("announces itself as a search group", () => {
    bar();

    expect(
      screen.getByRole("search", { name: "Filtrer les missions" }),
    ).toBeInTheDocument();
  });
});
