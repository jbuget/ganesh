import { describe, expect, it, vi } from "vitest";
import { render, screen } from "@testing-library/react";

import { ChooseActivityDialog } from "./ChooseActivityDialog";

function show(activities: { id: number; label: string }[]) {
  render(
    <ChooseActivityDialog
      open
      onOpenChange={vi.fn()}
      mission="Sitetracker - GMAO"
      activities={activities}
      onChoose={vi.fn()}
    />,
  );
}

describe("ChooseActivityDialog", () => {
  it("asks to choose when the mission offers several trades", () => {
    show([
      { id: 1, label: "Développement" },
      { id: 2, label: "Pilotage" },
    ]);

    expect(
      screen.getByText(
        "« Sitetracker - GMAO » est découpé en plusieurs activités. Choisissez celle sous laquelle vous allez déclarer votre temps.",
      ),
    ).toBeInTheDocument();
  });

  it("says which trade the time goes under when a single one is left", () => {
    show([{ id: 1, label: "Développement" }]);

    expect(
      screen.getByText(
        "Votre temps sur « Sitetracker - GMAO » sera déclaré sous cette activité.",
      ),
    ).toBeInTheDocument();
  });
});
