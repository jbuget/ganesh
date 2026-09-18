import { describe, expect, it, vi } from "vitest";
import { fireEvent, render, screen } from "@testing-library/react";

import { MissionFilters } from "./MissionFilters";
import { NO_FILTER, type MissionFilters as Criteres } from "@/lib/mission-filters";

vi.mock("@/lib/api/queries", () => ({
  useTeammates: () => ({
    teammates: [{ id: 3, display_name: "Nino Bosc", initials: "NB" }],
  }),
}));

const barre = (over: Partial<Criteres> = {}, props: Record<string, unknown> = {}) => {
  const filters = { ...NO_FILTER, ...over };
  const onChange = vi.fn();
  const onEffacer = vi.fn();
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
      onEffacer={onEffacer}
      visible={3}
      total={12}
      {...props}
    />,
  );
  return { onChange, onEffacer };
};

describe("MissionFilters", () => {
  it("offers the five criteria", () => {
    barre();

    expect(screen.getByLabelText("Rechercher une mission")).toBeInTheDocument();
    ["Phase", "Catégorie", "Priorité", "Intervenant", "Type", "État"].forEach(
      (critere) => {
        expect(
          screen.getByRole("button", { name: new RegExp(critere) }),
        ).toBeInTheDocument();
      },
    );
  });

  it("reports the search typed", () => {
    const { onChange } = barre();

    fireEvent.change(screen.getByLabelText("Rechercher une mission"), {
      target: { value: "portail" },
    });

    expect(onChange).toHaveBeenCalledWith({ name: "portail" });
  });

  it("reports a ticked phase", () => {
    const { onChange } = barre();

    fireEvent.click(screen.getByRole("button", { name: /Phase/ }));
    fireEvent.click(screen.getByRole("button", { name: "Réalisation" }));

    expect(onChange).toHaveBeenCalledWith({ phases: ["development"] });
  });

  it("reports a ticked contributor, by their id", () => {
    const { onChange } = barre();

    fireEvent.click(screen.getByRole("button", { name: /Intervenant/ }));
    fireEvent.click(screen.getByRole("button", { name: /Nino Bosc/ }));

    expect(onChange).toHaveBeenCalledWith({ contributors: [3] });
  });

  it("tells projects from sub-projects", () => {
    const { onChange } = barre();

    fireEvent.click(screen.getByRole("button", { name: /Type/ }));
    fireEvent.click(screen.getByRole("button", { name: "Sous-projets" }));

    expect(onChange).toHaveBeenCalledWith({ types: ["work_package"] });
  });

  it("reports a ticked priority", () => {
    const { onChange } = barre();

    fireEvent.click(screen.getByRole("button", { name: /Priorité/ }));
    fireEvent.click(screen.getByRole("button", { name: "Critique" }));

    expect(onChange).toHaveBeenCalledWith({ priorities: ["critical"] });
  });

  it("offers to look at archived missions", () => {
    const { onChange } = barre();

    fireEvent.click(screen.getByRole("button", { name: /État/ }));
    fireEvent.click(screen.getByRole("button", { name: "Archivées" }));

    expect(onChange).toHaveBeenCalledWith({ states: ["archivee"] });
  });

  it("offers to clear only when there is something to clear", () => {
    barre();

    expect(screen.queryByRole("button", { name: "Effacer" })).toBeNull();
  });

  it("clears every criterion in one click", () => {
    const { onEffacer } = barre({ name: "portail" });

    fireEvent.click(screen.getByRole("button", { name: "Effacer" }));

    expect(onEffacer).toHaveBeenCalledTimes(1);
  });

  it("says what is seen against what the screen carries", () => {
    barre({ phases: ["scoping"] });

    expect(screen.getByRole("status")).toHaveTextContent("3 missions sur 12");
  });

  it("announces itself as a search group", () => {
    barre();

    expect(
      screen.getByRole("search", { name: "Filtrer les missions" }),
    ).toBeInTheDocument();
  });
});
