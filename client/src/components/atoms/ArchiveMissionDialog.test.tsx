import { describe, expect, it, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import { ArchiveMissionDialog } from "./ArchiveMissionDialog";

function open(props: Partial<React.ComponentProps<typeof ArchiveMissionDialog>> = {}) {
  const onConfirm = vi.fn();
  render(
    <ArchiveMissionDialog
      open
      onOpenChange={vi.fn()}
      label="EDIT"
      subProjects={3}
      onConfirm={onConfirm}
      {...props}
    />,
  );
  return { onConfirm };
}

describe("ArchiveMissionDialog", () => {
  it("counts the packages the archiving would leave behind", () => {
    open();

    expect(screen.getByText("« EDIT » porte 3 sous-projets.")).toBeInTheDocument();
  });

  it("agrees what it says to a single package", () => {
    open({ subProjects: 1 });

    expect(screen.getByText("« EDIT » porte un sous-projet.")).toBeInTheDocument();
    expect(screen.getByText(/qu'il devient/)).toBeInTheDocument();
  });

  it("takes the packages out with the project", async () => {
    const { onConfirm } = open();

    await userEvent.click(
      screen.getByRole("button", { name: /Archiver aussi les 3 sous-projets/ }),
    );

    expect(onConfirm).toHaveBeenCalledWith("archive");
  });

  it("leaves the packages running as projects of their own", async () => {
    const { onConfirm } = open();

    await userEvent.click(
      screen.getByRole("button", { name: /Les détacher en projets autonomes/ }),
    );

    expect(onConfirm).toHaveBeenCalledWith("detach");
  });

  /** What detaching costs is read before it is chosen, not after. */
  it("says the archived project will no longer count their days", () => {
    open();

    expect(screen.getByText(/ne comptera plus leurs jours/)).toBeInTheDocument();
  });

  /** Dealing with a package by hand first is always an option. */
  it("leaves a way out that archives nothing", async () => {
    const { onConfirm } = open();

    await userEvent.click(screen.getByRole("button", { name: "Annuler" }));

    expect(onConfirm).not.toHaveBeenCalled();
  });
});
