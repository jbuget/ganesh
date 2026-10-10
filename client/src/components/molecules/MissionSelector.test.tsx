import { describe, expect, it, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import { MissionSelector } from "./MissionSelector";
import type { ProjectListItemResponse } from "@/lib/api/generated/model";

const trade = (id: number, projectId: number, label: string) => ({
  id,
  project_id: projectId,
  label,
  nature: "development",
  estimated_days: null,
  is_active: true,
  entries: 0,
});

const mission = (
  id: number,
  label: string,
  trades: { id: number; label: string }[],
  kind: "project" | "off_project" = "project",
): ProjectListItemResponse =>
  ({
    project: {
      id,
      label,
      kind,
      status: "scoping",
      parent_id: null,
      is_active: true,
      estimated_days: null,
      is_syncable_to_monday: false,
    },
    activities: trades.map((one) => trade(one.id, id, one.label)),
  }) as unknown as ProjectListItemResponse;

const MISSIONS: ProjectListItemResponse[] = [
  mission(1, "Sitetracker - GMAO", [
    { id: 10, label: "Design" },
    { id: 11, label: "Développement" },
    { id: 12, label: "Pilotage" },
  ]),
  mission(2, "Portail bailleurs", [{ id: 20, label: "Développement" }]),
  mission(3, "Absences", [], "off_project"),
];

function open(props: Partial<Parameters<typeof MissionSelector>[0]> = {}) {
  const onSelect = vi.fn();
  render(
    <MissionSelector
      missions={MISSIONS}
      excludedKeys={[]}
      assignedIds={[]}
      onSelect={onSelect}
      onDeclareNew={vi.fn()}
      {...props}
    />,
  );
  return { onSelect, user: userEvent.setup() };
}

describe("MissionSelector", () => {
  it("exposes a named picker", () => {
    open();

    expect(
      screen.getByRole("combobox", { name: "Ajouter un projet" }),
    ).toBeInTheDocument();
  });

  it("invites adding a mission", () => {
    open();

    expect(screen.getByText(/Ajouter un projet/)).toBeInTheDocument();
  });

  it("is disabled when the month is locked", () => {
    open({ disabled: true });

    expect(screen.getByRole("combobox")).toBeDisabled();
  });

  it("asks which trade when the mission carries several", async () => {
    const { onSelect, user } = open();

    await user.click(screen.getByRole("combobox", { name: "Ajouter un projet" }));
    await user.click(await screen.findByText("Sitetracker - GMAO"));

    expect(await screen.findByText("Sous quelle activité ?")).toBeInTheDocument();
    expect(onSelect).not.toHaveBeenCalled();

    await user.click(screen.getByRole("button", { name: "Design" }));

    expect(onSelect).toHaveBeenCalledWith(1, 10);
  });

  /**
   * The gesture the hover panel used to lose: choosing a mission closed the
   * list, and the trades went with it before the click could land.
   */
  it("still asks when one of the trades is already on the month", async () => {
    const { onSelect, user } = open({ excludedKeys: ["1:11"] });

    await user.click(screen.getByRole("combobox", { name: "Ajouter un projet" }));
    await user.click(await screen.findByText("Sitetracker - GMAO"));

    expect(
      screen.queryByRole("button", { name: "Développement" }),
    ).not.toBeInTheDocument();

    await user.click(screen.getByRole("button", { name: "Design" }));

    expect(onSelect).toHaveBeenCalledWith(1, 10);
  });

  it("adds a mission carrying a single trade without asking", async () => {
    const { onSelect, user } = open();

    await user.click(screen.getByRole("combobox", { name: "Ajouter un projet" }));
    await user.click(await screen.findByText("Portail bailleurs"));

    expect(screen.queryByText("Sous quelle activité ?")).not.toBeInTheDocument();
    expect(onSelect).toHaveBeenCalledWith(2, 20);
  });

  it("adds off-project work as itself, under no trade", async () => {
    const { onSelect, user } = open();

    await user.click(screen.getByRole("combobox", { name: "Ajouter un projet" }));
    await user.click(await screen.findByText("Absences"));

    expect(onSelect).toHaveBeenCalledWith(3, null);
  });
});
