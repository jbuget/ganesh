import { describe, expect, it, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import { DeclareProjectDialog } from "./DeclareProjectDialog";

describe("DeclareProjectDialog", () => {
  it("declares a project on the name given", async () => {
    const confirm = vi.fn();
    render(<DeclareProjectDialog open onOpenChange={vi.fn()} onConfirm={confirm} />);

    await userEvent.type(
      screen.getByLabelText("Nom du projet"),
      "  Refonte extranet  ",
    );
    await userEvent.click(screen.getByRole("button", { name: "Déclarer" }));

    expect(confirm).toHaveBeenCalledWith("Refonte extranet");
  });

  it("refuses to declare anything without a name", async () => {
    const confirm = vi.fn();
    render(<DeclareProjectDialog open onOpenChange={vi.fn()} onConfirm={confirm} />);

    expect(screen.getByRole("button", { name: "Déclarer" })).toBeDisabled();
    expect(confirm).not.toHaveBeenCalled();
  });
});

/**
 * One name is all either asks for, and neither is announced the way the other
 * is: a project joins the reference list, a package joins a project.
 */
describe("DeclareProjectDialog — what is being declared", () => {
  it("says the reference list where a project is declared", () => {
    render(<DeclareProjectDialog open onOpenChange={vi.fn()} onConfirm={vi.fn()} />);

    expect(
      screen.getByRole("heading", { name: "Déclarer un projet" }),
    ).toBeInTheDocument();
    expect(screen.getByText(/référentiel commun/)).toBeInTheDocument();
  });

  it("says the project a sub-project joins", () => {
    render(
      <DeclareProjectDialog
        open
        kind="work_package"
        onOpenChange={vi.fn()}
        onConfirm={vi.fn()}
      />,
    );

    expect(
      screen.getByRole("heading", { name: "Déclarer un sous-projet" }),
    ).toBeInTheDocument();
    expect(screen.getByLabelText("Nom du sous-projet")).toBeInTheDocument();
    expect(screen.getByText(/rattaché au projet/)).toBeInTheDocument();
  });
});
