import { describe, expect, it, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import { MissionMenu } from "./MissionMenu";

describe("MissionMenu", () => {
  it("keeps its actions folded until they are asked for", () => {
    render(
      <MissionMenu
        archived={false}
        onArchive={vi.fn()}
        onUnarchive={vi.fn()}
        onDelete={vi.fn()}
      />,
    );

    expect(
      screen.getByRole("button", { name: "Actions sur le projet" }),
    ).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "Archiver" })).toBeNull();
  });

  it("offers to archive the mission", async () => {
    render(
      <MissionMenu
        archived={false}
        onArchive={vi.fn()}
        onUnarchive={vi.fn()}
        onDelete={vi.fn()}
      />,
    );

    await userEvent.click(
      screen.getByRole("button", { name: "Actions sur le projet" }),
    );

    expect(screen.getByRole("button", { name: "Archiver" })).toBeInTheDocument();
  });

  it("archives the mission when the action is chosen", async () => {
    const archive = vi.fn();
    render(
      <MissionMenu
        archived={false}
        onArchive={archive}
        onUnarchive={vi.fn()}
        onDelete={vi.fn()}
      />,
    );

    await userEvent.click(
      screen.getByRole("button", { name: "Actions sur le projet" }),
    );
    await userEvent.click(screen.getByRole("button", { name: "Archiver" }));

    expect(archive).toHaveBeenCalledTimes(1);
  });

  it("closes the menu once the action is chosen", async () => {
    render(
      <MissionMenu
        archived={false}
        onArchive={vi.fn()}
        onUnarchive={vi.fn()}
        onDelete={vi.fn()}
      />,
    );

    await userEvent.click(
      screen.getByRole("button", { name: "Actions sur le projet" }),
    );
    await userEvent.click(screen.getByRole("button", { name: "Archiver" }));

    expect(screen.queryByRole("button", { name: "Archiver" })).toBeNull();
  });
  it("offers to unarchive a mission already out of the reference list", async () => {
    render(
      <MissionMenu
        archived
        onArchive={vi.fn()}
        onUnarchive={vi.fn()}
        onDelete={vi.fn()}
      />,
    );

    await userEvent.click(
      screen.getByRole("button", { name: "Actions sur le projet" }),
    );

    expect(screen.getByRole("button", { name: "Désarchiver" })).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "Archiver" })).toBeNull();
  });

  it("puts the mission back in the reference list when the action is chosen", async () => {
    const unarchive = vi.fn();
    render(
      <MissionMenu
        archived
        onArchive={vi.fn()}
        onUnarchive={unarchive}
        onDelete={vi.fn()}
      />,
    );

    await userEvent.click(
      screen.getByRole("button", { name: "Actions sur le projet" }),
    );
    await userEvent.click(screen.getByRole("button", { name: "Désarchiver" }));

    expect(unarchive).toHaveBeenCalledTimes(1);
  });

  /**
   * The mission that carries time gets the entry all the same: the dialog
   * behind it is what explains the refusal.
   */
  it("offers to delete the mission, under archiving", async () => {
    render(
      <MissionMenu
        archived={false}
        onArchive={vi.fn()}
        onUnarchive={vi.fn()}
        onDelete={vi.fn()}
      />,
    );

    await userEvent.click(
      screen.getByRole("button", { name: "Actions sur le projet" }),
    );

    const entries = screen.getAllByRole("listitem").map((entry) => entry.textContent);
    expect(entries).toEqual(["Archiver", "Supprimer"]);
  });

  it("asks to delete the mission when the action is chosen", async () => {
    const remove = vi.fn();
    render(
      <MissionMenu
        archived={false}
        onArchive={vi.fn()}
        onUnarchive={vi.fn()}
        onDelete={remove}
      />,
    );

    await userEvent.click(
      screen.getByRole("button", { name: "Actions sur le projet" }),
    );
    await userEvent.click(screen.getByRole("button", { name: "Supprimer" }));

    expect(remove).toHaveBeenCalledTimes(1);
  });

  /** The dialog takes over the screen: the menu must not stay under it. */
  it("closes the menu when the deletion is asked for", async () => {
    render(
      <MissionMenu
        archived={false}
        onArchive={vi.fn()}
        onUnarchive={vi.fn()}
        onDelete={vi.fn()}
      />,
    );

    await userEvent.click(
      screen.getByRole("button", { name: "Actions sur le projet" }),
    );
    await userEvent.click(screen.getByRole("button", { name: "Supprimer" }));

    expect(screen.queryByRole("button", { name: "Supprimer" })).toBeNull();
  });

  /**
   * Deleting an archived mission stays possible: archiving is not what makes
   * a mission un-deletable — the time it carries is.
   */
  it("keeps the deletion within reach on an archived mission", async () => {
    render(
      <MissionMenu
        archived
        onArchive={vi.fn()}
        onUnarchive={vi.fn()}
        onDelete={vi.fn()}
      />,
    );

    await userEvent.click(
      screen.getByRole("button", { name: "Actions sur le projet" }),
    );

    expect(screen.getByRole("button", { name: "Supprimer" })).toBeInTheDocument();
  });
});

describe("MissionMenu — where the mission sits", () => {
  it("offers to attach a mission that belongs to no project", async () => {
    const attach = vi.fn();
    render(
      <MissionMenu
        archived={false}
        onAttach={attach}
        onArchive={vi.fn()}
        onUnarchive={vi.fn()}
        onDelete={vi.fn()}
      />,
    );

    await userEvent.click(
      screen.getByRole("button", { name: "Actions sur le projet" }),
    );
    await userEvent.click(
      screen.getByRole("button", { name: "Rattacher à un projet…" }),
    );

    expect(attach).toHaveBeenCalledTimes(1);
  });

  it("names the project a work package would leave", async () => {
    const detach = vi.fn();
    render(
      <MissionMenu
        archived={false}
        onDetach={detach}
        parentLabel="EDIT"
        onArchive={vi.fn()}
        onUnarchive={vi.fn()}
        onDelete={vi.fn()}
      />,
    );

    await userEvent.click(
      screen.getByRole("button", { name: "Actions sur le projet" }),
    );
    await userEvent.click(screen.getByRole("button", { name: /Détacher de/ }));

    expect(detach).toHaveBeenCalledTimes(1);
  });

  it("says nothing of the hierarchy where the question does not arise", async () => {
    render(
      <MissionMenu
        archived={false}
        onArchive={vi.fn()}
        onUnarchive={vi.fn()}
        onDelete={vi.fn()}
      />,
    );

    await userEvent.click(
      screen.getByRole("button", { name: "Actions sur le projet" }),
    );

    expect(screen.queryByRole("button", { name: /Rattacher/ })).toBeNull();
    expect(screen.queryByRole("button", { name: /Détacher/ })).toBeNull();
  });
});

describe("MissionMenu — cutting a project into packages", () => {
  it("offers to declare a sub-project on a mission that can carry one", async () => {
    const declare = vi.fn();
    render(
      <MissionMenu
        archived={false}
        onAddSubProject={declare}
        onArchive={vi.fn()}
        onUnarchive={vi.fn()}
        onDelete={vi.fn()}
      />,
    );

    await userEvent.click(
      screen.getByRole("button", { name: "Actions sur le projet" }),
    );
    await userEvent.click(
      screen.getByRole("button", { name: "Déclarer un sous-projet…" }),
    );

    expect(declare).toHaveBeenCalledTimes(1);
  });

  /** The dialog takes over the screen: the menu must not stay under it. */
  it("closes the menu once the declaration is asked for", async () => {
    render(
      <MissionMenu
        archived={false}
        onAddSubProject={vi.fn()}
        onArchive={vi.fn()}
        onUnarchive={vi.fn()}
        onDelete={vi.fn()}
      />,
    );

    await userEvent.click(
      screen.getByRole("button", { name: "Actions sur le projet" }),
    );
    await userEvent.click(
      screen.getByRole("button", { name: "Déclarer un sous-projet…" }),
    );

    expect(
      screen.queryByRole("button", { name: "Déclarer un sous-projet…" }),
    ).toBeNull();
  });

  /** Creating comes before moving, and both before what takes the mission out. */
  it("reads before the entries that move the mission and those that take it out", async () => {
    render(
      <MissionMenu
        archived={false}
        onAddSubProject={vi.fn()}
        onAttach={vi.fn()}
        onArchive={vi.fn()}
        onUnarchive={vi.fn()}
        onDelete={vi.fn()}
      />,
    );

    await userEvent.click(
      screen.getByRole("button", { name: "Actions sur le projet" }),
    );

    const entries = screen.getAllByRole("listitem").map((entry) => entry.textContent);
    expect(entries).toEqual([
      "Déclarer un sous-projet…",
      "Rattacher à un projet…",
      "Archiver",
      "Supprimer",
    ]);
  });

  it("says nothing of it where the mission cannot carry a package", async () => {
    render(
      <MissionMenu
        archived={false}
        onArchive={vi.fn()}
        onUnarchive={vi.fn()}
        onDelete={vi.fn()}
      />,
    );

    await userEvent.click(
      screen.getByRole("button", { name: "Actions sur le projet" }),
    );

    expect(screen.queryByRole("button", { name: /sous-projet/ })).toBeNull();
  });
});
