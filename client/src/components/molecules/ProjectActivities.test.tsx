import { describe, expect, it, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import { ProjectActivities } from "./ProjectActivities";
import type { ActivityResponse } from "@/lib/api/generated/model";

const activity = (fields: Partial<ActivityResponse> = {}): ActivityResponse =>
  ({
    id: 100,
    project_id: 10,
    label: "Développement",
    nature: "development",
    estimated_days: 15,
    is_active: true,
    entries: 0,
    ...fields,
  }) as ActivityResponse;

const baseProps = {
  editable: true,
  onAdd: vi.fn(),
  onChange: vi.fn(),
  onArchive: vi.fn(),
  onRemove: vi.fn(),
  onUnarchive: vi.fn(),
};

describe("ProjectActivities", () => {
  it("says a mission with no activity cannot be declared on", () => {
    render(<ProjectActivities {...baseProps} activities={[]} />);

    expect(screen.getByText(/personne ne peut déclarer de temps/)).toBeInTheDocument();
  });

  it("names each trade and what it is budgeted at", () => {
    render(<ProjectActivities {...baseProps} activities={[activity()]} />);

    // The trade shows twice: as the row's own name, and among the buttons
    // that add one — so the row is found by what only it carries.
    expect(
      screen.getByRole("button", { name: "Retirer Développement" }),
    ).toBeInTheDocument();
    expect(screen.getByText(/15/)).toBeInTheDocument();
  });

  it("says when a trade carries no budget, because the ratio then waits", () => {
    render(
      <ProjectActivities
        {...baseProps}
        activities={[activity(), activity({ id: 101, estimated_days: null })]}
      />,
    );

    expect(screen.getByText(/le projet n'affiche pas de ratio/)).toBeInTheDocument();
  });

  it("offers the four trades, each named as the team names it", () => {
    render(<ProjectActivities {...baseProps} activities={[]} />);

    for (const trade of [
      "Développement",
      "Design",
      "Chefferie de projet",
      "Delivery",
    ]) {
      expect(screen.getByRole("button", { name: trade })).toBeInTheDocument();
    }
  });

  it("adds the trade one picks, named after it", async () => {
    const onAdd = vi.fn();
    render(<ProjectActivities {...baseProps} onAdd={onAdd} activities={[]} />);

    await userEvent.click(screen.getByRole("button", { name: "Delivery" }));

    expect(onAdd).toHaveBeenCalledWith("Delivery", "delivery");
  });

  it("says what withdrawing a trade would leave behind", () => {
    render(
      <ProjectActivities {...baseProps} activities={[activity({ entries: 12 })]} />,
    );

    expect(
      screen.getByRole("button", { name: "Retirer Développement" }),
    ).toHaveAttribute("title", "12 saisies restent lisibles");
  });

  it("archives a trade that carries days, and says nothing is erased", async () => {
    const onArchive = vi.fn();
    const onRemove = vi.fn();
    render(
      <ProjectActivities
        {...baseProps}
        onArchive={onArchive}
        onRemove={onRemove}
        activities={[activity({ entries: 12 })]}
      />,
    );

    await userEvent.click(
      screen.getByRole("button", { name: "Retirer Développement" }),
    );

    expect(screen.getByRole("alertdialog")).toHaveTextContent(/porte 12 saisies/);
    expect(screen.getByRole("alertdialog")).toHaveTextContent(/Rien n'est effacé/);

    await userEvent.click(screen.getByRole("button", { name: "Archiver l'activité" }));

    expect(onArchive).toHaveBeenCalledWith(100);
    expect(onRemove).not.toHaveBeenCalled();
  });

  it("deletes a trade nobody declared on", async () => {
    const onArchive = vi.fn();
    const onRemove = vi.fn();
    render(
      <ProjectActivities
        {...baseProps}
        onArchive={onArchive}
        onRemove={onRemove}
        activities={[activity({ entries: 0 })]}
      />,
    );

    await userEvent.click(
      screen.getByRole("button", { name: "Retirer Développement" }),
    );
    await userEvent.click(screen.getByRole("button", { name: "Supprimer l'activité" }));

    expect(onRemove).toHaveBeenCalledWith(100);
    expect(onArchive).not.toHaveBeenCalled();
  });

  it("does not offer a trade the mission already carries", () => {
    render(<ProjectActivities {...baseProps} activities={[activity()]} />);

    const already = screen.getByRole("button", { name: "Développement" });
    expect(already).toBeDisabled();
    expect(screen.getByRole("button", { name: "Design" })).toBeEnabled();
  });

  it("offers a trade again once its activity is archived", () => {
    render(
      <ProjectActivities
        {...baseProps}
        activities={[activity({ is_active: false })]}
      />,
    );

    expect(screen.getByRole("button", { name: "Développement" })).toBeEnabled();
  });

  it("folds the archived trades away rather than dropping them", () => {
    render(
      <ProjectActivities
        {...baseProps}
        activities={[activity({ id: 101, label: "Design", is_active: false })]}
      />,
    );

    expect(screen.getByText("1 activité archivée")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Rouvrir Design" })).toBeInTheDocument();
  });
});

describe("ProjectActivities — what a guest may do", () => {
  it("offers no gesture: a guest declares nothing into Ganesh", () => {
    render(
      <ProjectActivities {...baseProps} editable={false} activities={[activity()]} />,
    );

    expect(screen.getByRole("button", { name: "Design" })).toBeDisabled();
    expect(
      screen.getByRole("button", { name: "Retirer Développement" }),
    ).toBeDisabled();
  });
});
