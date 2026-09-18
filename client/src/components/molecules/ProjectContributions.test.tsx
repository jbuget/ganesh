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
  it("announces that no time is declared", () => {
    render(<ProjectContributions contributions={[]} total={0} />);

    expect(screen.getByText("Aucun temps déclaré")).toBeInTheDocument();
  });

  it("unfolds a contributor's monthly detail", () => {
    render(
      <ProjectContributions contributions={[contribution(1, "Léa", 4)]} total={4} />,
    );

    fireEvent.click(screen.getByRole("button", { name: /Léa/ }));

    expect(screen.getByText("septembre 2026")).toBeInTheDocument();
  });

  it("keeps the other contributors open", () => {
    // Two people are expanded precisely to set their months side by side.
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

  it("closes one row without touching the others", () => {
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
