import { describe, expect, it, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import { AssignedMissionsCallout } from "./AssignedMissionsCallout";

const MISSIONS = [
  {
    id: 1,
    label: "Portail bailleurs",
    activities: [{ id: 100, label: "Développement" }],
  },
  { id: 3, label: "Lot 1", activities: [{ id: 300, label: "Développement" }] },
];

describe("AssignedMissionsCallout", () => {
  it("counts the projects left to declare", () => {
    render(<AssignedMissionsCallout missions={MISSIONS} onAdd={vi.fn()} />);

    expect(screen.getByRole("status")).toHaveTextContent(
      "Vous êtes déclaré en tant qu'intervenant sur 2 projets sans temps saisi ce mois-ci",
    );
  });

  it("speaks of a single project in the singular", () => {
    render(<AssignedMissionsCallout missions={[MISSIONS[0]]} onAdd={vi.fn()} />);

    expect(screen.getByRole("status")).toHaveTextContent(
      "Vous êtes déclaré en tant qu'intervenant sur 1 projet sans temps saisi ce mois-ci",
    );
  });

  it("adds the mission one picks", async () => {
    const onAdd = vi.fn();
    render(<AssignedMissionsCallout missions={MISSIONS} onAdd={onAdd} />);

    await userEvent.click(screen.getByRole("button", { name: "Ajouter Lot 1" }));

    // A single trade is added straight away: a dialog offering one button
    // takes a click from the reader for nothing.
    expect(onAdd).toHaveBeenCalledWith(3, 300);
  });

  it("says nothing when there is nothing to add", () => {
    const { container } = render(
      <AssignedMissionsCallout missions={[]} onAdd={vi.fn()} />,
    );

    expect(container).toBeEmptyDOMElement();
  });
  it("asks which trade when the mission carries several", async () => {
    const onAdd = vi.fn();
    render(
      <AssignedMissionsCallout
        missions={[
          {
            id: 7,
            label: "Watom",
            activities: [
              { id: 700, label: "Développement" },
              { id: 701, label: "Chefferie de projet" },
            ],
          },
        ]}
        onAdd={onAdd}
      />,
    );

    await userEvent.click(screen.getByRole("button", { name: "Ajouter Watom" }));
    expect(onAdd).not.toHaveBeenCalled();

    await userEvent.click(screen.getByRole("button", { name: "Chefferie de projet" }));

    expect(onAdd).toHaveBeenCalledWith(7, 701);
  });

  it("offers nothing on a mission nobody has cut up", () => {
    render(
      <AssignedMissionsCallout
        missions={[{ id: 9, label: "Neuf", activities: [] }]}
        onAdd={vi.fn()}
      />,
    );

    expect(screen.getByRole("button", { name: "Ajouter Neuf" })).toBeDisabled();
  });
});
