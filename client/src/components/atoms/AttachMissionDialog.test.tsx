import { describe, expect, it, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import { AttachMissionDialog } from "./AttachMissionDialog";

vi.mock("@/lib/api/queries", () => ({
  useProjects: () => ({
    missions: [
      { project: { id: 10, label: "EDIT", kind: "project" } },
      { project: { id: 11, label: "Portail bailleurs", kind: "project" } },
      { project: { id: 12, label: "DOE", kind: "work_package", parent_id: 10 } },
      { project: { id: 13, label: "Absences", kind: "off_project" } },
      { project: { id: 20, label: "EDIT V1", kind: "project" } },
    ],
  }),
}));

function open(props: Record<string, unknown> = {}) {
  const onConfirm = vi.fn();
  const onOpenChange = vi.fn();
  render(
    <AttachMissionDialog
      open
      onOpenChange={onOpenChange}
      missionId={20}
      label="EDIT V1"
      subProjects={0}
      published={false}
      onConfirm={onConfirm}
      {...props}
    />,
  );
  return { onConfirm, onOpenChange };
}

describe("AttachMissionDialog", () => {
  it("offers the projects a mission may become a slice of", () => {
    open();

    expect(screen.getByRole("button", { name: "EDIT" })).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: "Portail bailleurs" }),
    ).toBeInTheDocument();
  });

  it("offers neither a work package nor off-project work", () => {
    open();

    expect(screen.queryByRole("button", { name: "DOE" })).toBeNull();
    expect(screen.queryByRole("button", { name: "Absences" })).toBeNull();
  });

  it("never offers the mission its own project", () => {
    open();

    expect(screen.queryByRole("button", { name: "EDIT V1" })).toBeNull();
  });

  it("leaves out the project the mission already belongs to", () => {
    open({ currentParentId: 10 });

    expect(screen.queryByRole("button", { name: "EDIT" })).toBeNull();
    expect(
      screen.getByRole("button", { name: "Portail bailleurs" }),
    ).toBeInTheDocument();
  });

  it("narrows the list as one types", async () => {
    open();

    await userEvent.type(screen.getByLabelText("Rechercher un projet"), "port");

    expect(
      screen.getByRole("button", { name: "Portail bailleurs" }),
    ).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "EDIT" })).toBeNull();
  });

  it("attaches the mission to the project that is chosen", async () => {
    const { onConfirm } = open();

    await userEvent.click(screen.getByRole("button", { name: "EDIT" }));

    expect(onConfirm).toHaveBeenCalledWith(10);
  });

  it("closes once the mission is attached", async () => {
    const { onOpenChange } = open();

    await userEvent.click(screen.getByRole("button", { name: "EDIT" }));

    expect(onOpenChange).toHaveBeenCalledWith(false);
  });

  it("explains why a mission carrying sub-projects cannot move", () => {
    open({ subProjects: 2 });

    expect(screen.getByText(/deux niveaux/)).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "EDIT" })).toBeNull();
  });

  it("explains that a published mission would lose its catalogue card", () => {
    open({ published: true });

    expect(screen.getByText(/publiée au catalogue/)).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "EDIT" })).toBeNull();
  });
});
