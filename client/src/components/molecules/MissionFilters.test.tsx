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
  it("propose les cinq critères", () => {
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

  it("remonte la recherche saisie", () => {
    const { onChange } = barre();

    fireEvent.change(screen.getByLabelText("Rechercher une mission"), {
      target: { value: "portail" },
    });

    expect(onChange).toHaveBeenCalledWith({ name: "portail" });
  });

  it("remonte une phase cochée", () => {
    const { onChange } = barre();

    fireEvent.click(screen.getByRole("button", { name: /Phase/ }));
    fireEvent.click(screen.getByRole("button", { name: "Réalisation" }));

    expect(onChange).toHaveBeenCalledWith({ phases: ["development"] });
  });

  it("remonte un intervenant coché, par son identifiant", () => {
    const { onChange } = barre();

    fireEvent.click(screen.getByRole("button", { name: /Intervenant/ }));
    fireEvent.click(screen.getByRole("button", { name: /Nino Bosc/ }));

    expect(onChange).toHaveBeenCalledWith({ contributors: [3] });
  });

  it("distingue les projets des sous-projets", () => {
    const { onChange } = barre();

    fireEvent.click(screen.getByRole("button", { name: /Type/ }));
    fireEvent.click(screen.getByRole("button", { name: "Sous-projets" }));

    expect(onChange).toHaveBeenCalledWith({ types: ["work_package"] });
  });

  it("remonte une priorité cochée", () => {
    const { onChange } = barre();

    fireEvent.click(screen.getByRole("button", { name: /Priorité/ }));
    fireEvent.click(screen.getByRole("button", { name: "Critique" }));

    expect(onChange).toHaveBeenCalledWith({ priorities: ["critical"] });
  });

  it("propose de consulter les missions archivées", () => {
    const { onChange } = barre();

    fireEvent.click(screen.getByRole("button", { name: /État/ }));
    fireEvent.click(screen.getByRole("button", { name: "Archivées" }));

    expect(onChange).toHaveBeenCalledWith({ states: ["archivee"] });
  });

  it("n'offre d'effacer que lorsqu'il y a quelque chose à effacer", () => {
    barre();

    expect(screen.queryByRole("button", { name: "Effacer" })).toBeNull();
  });

  it("efface tous les critères d'un clic", () => {
    const { onEffacer } = barre({ name: "portail" });

    fireEvent.click(screen.getByRole("button", { name: "Effacer" }));

    expect(onEffacer).toHaveBeenCalledTimes(1);
  });

  it("dit ce qu'on voit sur ce que l'écran porte", () => {
    barre({ phases: ["scoping"] });

    expect(screen.getByRole("status")).toHaveTextContent("3 missions sur 12");
  });

  it("s'annonce comme un groupe de recherche", () => {
    barre();

    expect(
      screen.getByRole("search", { name: "Filtrer les missions" }),
    ).toBeInTheDocument();
  });
});
