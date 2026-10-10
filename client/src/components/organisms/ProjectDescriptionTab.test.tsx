import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

import { ProjectDescriptionTab } from "@/components/organisms/ProjectDescriptionTab";

describe("ProjectDescriptionTab", () => {
  it("invites writing the sheet when there is none", () => {
    render(
      <ProjectDescriptionTab
        description={null}
        saveDescription={vi.fn().mockResolvedValue(undefined)}
      />,
    );

    expect(screen.getByText(/Aucune fiche/)).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: "Rédiger la fiche" }),
    ).toBeInTheDocument();
  });

  it("reads the description rendered, and offers to change it", () => {
    render(
      <ProjectDescriptionTab
        description="Un portail pour les bailleurs"
        saveDescription={vi.fn().mockResolvedValue(undefined)}
      />,
    );

    expect(screen.getByText("Un portail pour les bailleurs")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Modifier" })).toBeInTheDocument();
  });

  it("opens the editor on demand", async () => {
    render(
      <ProjectDescriptionTab
        description="Un portail"
        saveDescription={vi.fn().mockResolvedValue(undefined)}
      />,
    );

    await userEvent.click(screen.getByRole("button", { name: "Modifier" }));

    expect(screen.getByRole("button", { name: "Enregistrer" })).toBeInTheDocument();
  });
});
