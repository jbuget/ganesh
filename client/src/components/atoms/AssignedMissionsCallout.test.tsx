import { describe, expect, it, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import { AssignedMissionsCallout } from "./AssignedMissionsCallout";

const MISSIONS = [
  { id: 1, label: "Portail bailleurs" },
  { id: 3, label: "Lot 1" },
];

describe("AssignedMissionsCallout", () => {
  it("counts the missions left to declare", () => {
    render(<AssignedMissionsCallout missions={MISSIONS} onAdd={vi.fn()} />);

    expect(screen.getByRole("status")).toHaveTextContent(
      "Vous intervenez sur 2 missions sans temps déclaré ce mois-ci",
    );
  });

  it("speaks of a single mission in the singular", () => {
    render(<AssignedMissionsCallout missions={[MISSIONS[0]]} onAdd={vi.fn()} />);

    expect(screen.getByRole("status")).toHaveTextContent(
      "Vous intervenez sur 1 mission sans temps déclaré ce mois-ci",
    );
  });

  it("adds the mission one picks", async () => {
    const onAdd = vi.fn();
    render(<AssignedMissionsCallout missions={MISSIONS} onAdd={onAdd} />);

    await userEvent.click(screen.getByRole("button", { name: "Ajouter Lot 1" }));

    expect(onAdd).toHaveBeenCalledWith(3);
  });

  it("says nothing when there is nothing to add", () => {
    const { container } = render(
      <AssignedMissionsCallout missions={[]} onAdd={vi.fn()} />,
    );

    expect(container).toBeEmptyDOMElement();
  });
});
