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
      screen.getByRole("button", { name: "Actions sur la mission" }),
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
      screen.getByRole("button", { name: "Actions sur la mission" }),
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
      screen.getByRole("button", { name: "Actions sur la mission" }),
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
      screen.getByRole("button", { name: "Actions sur la mission" }),
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
      screen.getByRole("button", { name: "Actions sur la mission" }),
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
      screen.getByRole("button", { name: "Actions sur la mission" }),
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
      screen.getByRole("button", { name: "Actions sur la mission" }),
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
      screen.getByRole("button", { name: "Actions sur la mission" }),
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
      screen.getByRole("button", { name: "Actions sur la mission" }),
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
      screen.getByRole("button", { name: "Actions sur la mission" }),
    );

    expect(screen.getByRole("button", { name: "Supprimer" })).toBeInTheDocument();
  });
});
