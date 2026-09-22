import { describe, expect, it, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import { DeleteMissionDialog } from "./DeleteMissionDialog";

function open(props: Partial<React.ComponentProps<typeof DeleteMissionDialog>> = {}) {
  const onConfirm = vi.fn();
  render(
    <DeleteMissionDialog
      open
      onOpenChange={vi.fn()}
      label="Portail"
      deletable
      consumedDays={0}
      subProjects={0}
      published={false}
      onConfirm={onConfirm}
      {...props}
    />,
  );
  return { onConfirm };
}

describe("DeleteMissionDialog", () => {
  it("asks to confirm a mission that never served", () => {
    open();

    expect(screen.getByText("Supprimer « Portail » ?")).toBeInTheDocument();
    expect(screen.getByText(/définitive/)).toBeInTheDocument();
  });

  /** The thread goes with the mission, which is not obvious from the menu. */
  it("warns that the follow-up thread goes too", () => {
    open();

    expect(screen.getByText(/mises à jour/)).toBeInTheDocument();
  });

  /**
   * The bytes go with it, and nothing else in the product holds a copy. A
   * confirmation that listed only the thread understated what the click costs.
   */
  it("warns that the files dropped on it go too", () => {
    open();

    expect(screen.getByText(/fichiers/)).toBeInTheDocument();
  });

  it("deletes the mission once confirmed", async () => {
    const { onConfirm } = open();

    await userEvent.click(screen.getByRole("button", { name: "Supprimer le projet" }));

    expect(onConfirm).toHaveBeenCalledTimes(1);
  });

  it("agrees the count it announces", () => {
    open({ deletable: false, consumedDays: 1 });

    expect(screen.getByText(/1 jour saisi :/)).toBeInTheDocument();
  });

  it("refuses a mission that carries time, and says how much", () => {
    open({ deletable: false, consumedDays: 3.5 });

    expect(screen.getByText("Suppression impossible")).toBeInTheDocument();
    expect(screen.getByText(/3,5 jours saisis/)).toBeInTheDocument();
  });

  /** Archiving is the way out: it is named rather than left to be guessed. */
  it("points to archiving when the time blocks the deletion", () => {
    open({ deletable: false, consumedDays: 1 });

    expect(screen.getByText(/[Aa]rchiv/)).toBeInTheDocument();
  });

  it("refuses a mission that carries work packages, and counts them", () => {
    open({ deletable: false, subProjects: 2 });

    expect(screen.getByText(/2 sous-projets/)).toBeInTheDocument();
  });

  /**
   * The project declared nothing itself; a package under it may have. Saying
   * « il y a du temps » here would send one looking for entries that are not
   * on this sheet.
   */
  it("blames the work packages, not time the mission never carried", () => {
    open({ deletable: false, consumedDays: 0, subProjects: 1 });

    expect(screen.getByText(/qui peut lui-même porter du temps/)).toBeInTheDocument();
    expect(screen.queryByText(/effacerait du temps déclaré/)).toBeNull();
  });

  /**
   * Archiving the project would leave the package right where it is: it is
   * not the way out of this one.
   */
  it("points to the work packages themselves, not to archiving", () => {
    open({ deletable: false, consumedDays: 0, subProjects: 1 });

    expect(screen.queryByText(/[Aa]rchiv/)).toBeNull();
    expect(screen.getByText(/Traitez-le d'abord/)).toBeInTheDocument();
  });

  it("names both obstacles when the mission carries both", () => {
    open({ deletable: false, consumedDays: 4, subProjects: 1 });

    expect(screen.getByText(/4 jours saisis/)).toBeInTheDocument();
    expect(screen.getByText(/un sous-projet/)).toBeInTheDocument();
  });

  /**
   * A published mission is an address somebody may have kept. Dropping its
   * card off waat.tools must be a decision of its own, taken beforehand.
   */
  it("refuses a published mission, and names where to unpublish it", () => {
    open({ deletable: false, published: true });

    expect(screen.getByText("Suppression impossible")).toBeInTheDocument();
    expect(screen.getByText(/publié au catalogue/)).toBeInTheDocument();
    expect(screen.getByText(/Dépubliez-le/)).toBeInTheDocument();
  });

  /**
   * On a mission that carries time, archiving is the whole answer: the
   * catalogue keeps the card and marks it archived. Sending one to unpublish
   * first would add a step that changes nothing.
   */
  it("says the time before the publication when it carries both", () => {
    open({ deletable: false, consumedDays: 2, published: true });

    expect(screen.getByText(/2 jours saisis/)).toBeInTheDocument();
    expect(screen.queryByText(/Dépubliez-le/)).toBeNull();
  });

  /** Nothing can be done from here: the only way out is closing. */
  it("offers no deletion when it is refused", () => {
    open({ deletable: false, consumedDays: 1 });

    expect(screen.queryByRole("button", { name: "Supprimer le projet" })).toBeNull();
    expect(screen.getByRole("button", { name: "Fermer" })).toBeInTheDocument();
  });
});
