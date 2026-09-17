import { describe, expect, it } from "vitest";
import { fireEvent, render, screen } from "@testing-library/react";

import { ProjectContributions } from "./ProjectContributions";
import type { ProjectContributionResponse } from "@/lib/api/generated/model";

const contribution = (
  id: number,
  name: string,
  days: number,
): ProjectContributionResponse =>
  ({
    member: { id, display_name: name, initials: name.slice(0, 2).toUpperCase() },
    days,
    by_month: [
      { month: "2026-09-01", days: days / 2 },
      { month: "2026-08-01", days: days / 2 },
    ],
  }) as ProjectContributionResponse;

describe("ProjectContributions", () => {
  it("annonce qu'aucun temps n'est déclaré", () => {
    render(<ProjectContributions contributions={[]} total={0} />);

    expect(screen.getByText("Aucun temps déclaré")).toBeInTheDocument();
  });

  it("déplie le détail mensuel d'un intervenant", () => {
    render(
      <ProjectContributions contributions={[contribution(1, "Léa", 4)]} total={4} />,
    );

    fireEvent.click(screen.getByRole("button", { name: /Léa/ }));

    expect(screen.getByText("septembre 2026")).toBeInTheDocument();
  });

  it("garde les autres intervenants ouverts", () => {
    // On deplie deux personnes justement pour confronter leurs mois.
    render(
      <ProjectContributions
        contributions={[contribution(1, "Léa", 4), contribution(2, "Nino", 2)]}
        total={6}
      />,
    );

    fireEvent.click(screen.getByRole("button", { name: /Léa/ }));
    fireEvent.click(screen.getByRole("button", { name: /Nino/ }));

    expect(screen.getAllByText("septembre 2026")).toHaveLength(2);
  });

  it("referme une ligne sans toucher aux autres", () => {
    render(
      <ProjectContributions
        contributions={[contribution(1, "Léa", 4), contribution(2, "Nino", 2)]}
        total={6}
      />,
    );
    fireEvent.click(screen.getByRole("button", { name: /Léa/ }));
    fireEvent.click(screen.getByRole("button", { name: /Nino/ }));

    fireEvent.click(screen.getByRole("button", { name: /Léa/ }));

    expect(screen.getAllByText("septembre 2026")).toHaveLength(1);
  });
});
