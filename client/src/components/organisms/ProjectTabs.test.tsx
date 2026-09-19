import { describe, expect, it, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import { ProjectTabs } from "./ProjectTabs";
import type { ProjectDetailResponse } from "@/lib/api/generated/model";

/** The four facets have their own tests: the deletion is what is asked here. */
vi.mock("@/components/organisms/ProjectSteeringTab", () => ({
  ProjectSteeringTab: () => <div />,
}));
vi.mock("@/components/organisms/ProjectSheetTab", () => ({
  ProjectSheetTab: () => <div />,
}));
vi.mock("@/components/organisms/ProjectUpdatesTab", () => ({
  ProjectUpdatesTab: () => <div />,
}));

function sheet(project: { is_deletable: boolean; consumed_days: number }) {
  return {
    project: {
      id: 10,
      label: "Portail",
      is_active: true,
      is_deletable: project.is_deletable,
      archived_at: null,
    },
    consumed_days: project.consumed_days,
    sub_projects: [],
    links: [],
    phases: [],
    leads: [],
    contributors: [],
    contributions: [],
    stack: [],
    tags: [],
    dependencies: [],
    departments: [],
    parent: null,
  } as unknown as ProjectDetailResponse;
}

function tabs(project: { is_deletable: boolean; consumed_days: number }) {
  const deleteMission = vi.fn();
  render(
    <ProjectTabs
      detail={sheet(project)}
      onChange={vi.fn()}
      saveSheet={vi.fn()}
      saveDescription={vi.fn()}
      changePhase={vi.fn()}
      updateFields={vi.fn()}
      saveRegistry={vi.fn()}
      addLink={vi.fn()}
      removeLink={vi.fn()}
      addSubProject={vi.fn()}
      attachTo={vi.fn()}
      detach={vi.fn()}
      archive={vi.fn()}
      unarchive={vi.fn()}
      deleteMission={deleteMission}
    />,
  );
  return { deleteMission };
}

async function askToDelete() {
  await userEvent.click(screen.getByRole("button", { name: "Actions sur la mission" }));
  await userEvent.click(screen.getByRole("button", { name: "Supprimer" }));
}

describe("ProjectTabs", () => {
  it("confirms before deleting a mission that never served", async () => {
    const { deleteMission } = tabs({ is_deletable: true, consumed_days: 0 });

    await askToDelete();
    expect(deleteMission).not.toHaveBeenCalled();

    await userEvent.click(screen.getByRole("button", { name: "Supprimer la mission" }));

    expect(deleteMission).toHaveBeenCalledTimes(1);
  });

  it("explains the refusal instead of deleting a mission that carries time", async () => {
    const { deleteMission } = tabs({ is_deletable: false, consumed_days: 2 });

    await askToDelete();

    expect(screen.getByText("Suppression impossible")).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "Supprimer la mission" })).toBeNull();
    expect(deleteMission).not.toHaveBeenCalled();
  });
});
