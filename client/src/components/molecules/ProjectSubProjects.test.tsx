import { describe, expect, it, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import { ProjectSubProjects } from "./ProjectSubProjects";
import type { ProjectResponse } from "@/lib/api/generated/model";

const workPackage = (id: number, label: string, status = "scoping"): ProjectResponse =>
  ({ id, label, status, kind: "work_package", parent_id: 10 }) as ProjectResponse;

const list = (subProjects: ProjectResponse[], onAdd = vi.fn()) => {
  render(<ProjectSubProjects subProjects={subProjects} onAdd={onAdd} />);
  return onAdd;
};

async function add(label: string) {
  await openTheForm();
  await userEvent.type(screen.getByLabelText("Nom du sous-projet"), label);
  await userEvent.click(screen.getByRole("button", { name: "Déclarer" }));
}

/**
 * The same entry as the one folded in the mission menu, word for word: two
 * ways in, one gesture, and nothing to tell apart once it is open.
 */
async function openTheForm() {
  await userEvent.click(
    screen.getByRole("button", { name: "Déclarer un sous-projet…" }),
  );
}

describe("ProjectSubProjects", () => {
  it("announces that no sub-project is attached", () => {
    list([]);

    expect(screen.getByText("Aucun sous-projet")).toBeInTheDocument();
  });

  it("leads to the sheet of each sub-project", () => {
    list([workPackage(11, "Authentification")]);

    expect(screen.getByRole("link", { name: /Authentification/ })).toHaveAttribute(
      "href",
      "/projects/11",
    );
  });

  it("says the phase of each sub-project", () => {
    list([
      workPackage(11, "Authentification"),
      workPackage(12, "Reprise", "development"),
    ]);

    expect(screen.getByText("Cadrage")).toBeInTheDocument();
    expect(screen.getByText("Réalisation")).toBeInTheDocument();
  });

  /**
   * Cutting a project into work packages happens while reading it, and comes
   * by three or four at a time at scoping. The entry therefore sits under the
   * list, where the packages already are.
   */
  it("attaches a sub-project to the mission", async () => {
    const onAdd = list([workPackage(11, "Authentification")]);

    await add("Reprise de données");

    expect(onAdd).toHaveBeenCalledWith("Reprise de données");
  });

  it("offers attaching one when none is attached yet", async () => {
    const onAdd = list([]);

    await add("Authentification");

    expect(onAdd).toHaveBeenCalledWith("Authentification");
  });

  it("refuses to attach a nameless sub-project", async () => {
    const onAdd = list([]);

    await openTheForm();

    expect(screen.getByRole("button", { name: "Déclarer" })).toBeDisabled();
    expect(onAdd).not.toHaveBeenCalled();
  });

  /** The dialog is the one the menu opens: it says what it is declaring. */
  it("declares the package under the project rather than beside it", async () => {
    list([]);

    await openTheForm();

    expect(
      screen.getByRole("heading", { name: "Déclarer un sous-projet" }),
    ).toBeInTheDocument();
    expect(screen.getByText(/rattaché au projet/)).toBeInTheDocument();
  });
});
