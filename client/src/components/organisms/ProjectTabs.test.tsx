import { describe, expect, it, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import { ProjectTabs } from "./ProjectTabs";
import type { ProjectDetailResponse } from "@/lib/api/generated/model";

/** The four facets have their own tests: the deletion is what is asked here. */
// The reading of « may this person write? » is its own hook, and its own
// tests: here it is answered yes, so that what is under test stays what the
// file says it is.
const mayWrite = vi.hoisted(() => ({ value: true }));
vi.mock("@/lib/use-may-write", () => ({ useMayWrite: () => mayWrite.value }));

vi.mock("@/components/organisms/ProjectSteeringTab", () => ({
  ProjectSteeringTab: () => <div />,
}));
vi.mock("@/components/organisms/ProjectSheetTab", () => ({
  ProjectSheetTab: () => <div />,
}));
vi.mock("@/components/organisms/ProjectUpdatesTab", () => ({
  ProjectUpdatesTab: () => <div />,
}));

interface Sheet {
  is_deletable: boolean;
  consumed_days: number;
  /** Work packages under the mission, told apart by whether they still run. */
  sub_projects?: { is_active: boolean }[];
  /** A project by default: it is the one kind that may carry packages. */
  kind?: "project" | "work_package" | "off_project";
}

function sheet(project: Sheet) {
  return {
    project: {
      id: 10,
      label: "Portail",
      kind: project.kind ?? "project",
      is_active: true,
      is_deletable: project.is_deletable,
      archived_at: null,
    },
    consumed_days: project.consumed_days,
    sub_projects: project.sub_projects ?? [],
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

function tabs(project: Sheet) {
  const deleteMission = vi.fn();
  const archive = vi.fn();
  const addSubProject = vi.fn();
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
      addSubProject={addSubProject}
      attachTo={vi.fn()}
      detach={vi.fn()}
      archive={archive}
      unarchive={vi.fn()}
      deleteMission={deleteMission}
    />,
  );
  return { deleteMission, archive, addSubProject };
}

async function askToDelete() {
  await userEvent.click(screen.getByRole("button", { name: "Actions sur le projet" }));
  await userEvent.click(screen.getByRole("button", { name: "Supprimer" }));
}

async function askToArchive() {
  await userEvent.click(screen.getByRole("button", { name: "Actions sur le projet" }));
  await userEvent.click(screen.getByRole("button", { name: "Archiver" }));
}

describe("ProjectTabs", () => {
  it("confirms before deleting a mission that never served", async () => {
    const { deleteMission } = tabs({ is_deletable: true, consumed_days: 0 });

    await askToDelete();
    expect(deleteMission).not.toHaveBeenCalled();

    await userEvent.click(screen.getByRole("button", { name: "Supprimer le projet" }));

    expect(deleteMission).toHaveBeenCalledTimes(1);
  });

  it("explains the refusal instead of deleting a mission that carries time", async () => {
    const { deleteMission } = tabs({ is_deletable: false, consumed_days: 2 });

    await askToDelete();

    expect(screen.getByText("Suppression impossible")).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "Supprimer le projet" })).toBeNull();
    expect(deleteMission).not.toHaveBeenCalled();
  });

  it("archives a mission carrying nothing without asking anything", async () => {
    const { archive } = tabs({ is_deletable: true, consumed_days: 0 });

    await askToArchive();

    expect(archive).toHaveBeenCalledWith();
  });

  it("asks what becomes of the packages before archiving their project", async () => {
    const { archive } = tabs({
      is_deletable: false,
      consumed_days: 4,
      sub_projects: [{ is_active: true }, { is_active: true }],
    });

    await askToArchive();
    expect(archive).not.toHaveBeenCalled();

    await userEvent.click(
      screen.getByRole("button", { name: /Les détacher en projets autonomes/ }),
    );

    expect(archive).toHaveBeenCalledWith("detach");
  });

  /** They left on their own account: there is nothing left to settle. */
  it("asks nothing over packages that already left", async () => {
    const { archive } = tabs({
      is_deletable: false,
      consumed_days: 4,
      sub_projects: [{ is_active: false }],
    });

    await askToArchive();

    expect(archive).toHaveBeenCalledWith();
  });
});

describe("ProjectTabs — cutting a project into packages", () => {
  it("declares a sub-project from the menu of the project", async () => {
    const { addSubProject } = tabs({ is_deletable: true, consumed_days: 0 });

    await userEvent.click(
      screen.getByRole("button", { name: "Actions sur le projet" }),
    );
    await userEvent.click(
      screen.getByRole("button", { name: "Déclarer un sous-projet…" }),
    );
    await userEvent.type(
      screen.getByLabelText("Nom du sous-projet"),
      "Reprise de données",
    );
    await userEvent.click(screen.getByRole("button", { name: "Déclarer" }));

    expect(addSubProject).toHaveBeenCalledWith("Reprise de données", null);
  });

  /** The hierarchy stops at two levels, and off-project work carries nothing. */
  it("offers nothing of the kind on a work package", async () => {
    tabs({ is_deletable: true, consumed_days: 0, kind: "work_package" });

    await userEvent.click(
      screen.getByRole("button", { name: "Actions sur le projet" }),
    );

    expect(
      screen.queryByRole("button", { name: /Déclarer un sous-projet/ }),
    ).toBeNull();
  });

  it("offers nothing of the kind on off-project work", async () => {
    tabs({ is_deletable: true, consumed_days: 0, kind: "off_project" });

    await userEvent.click(
      screen.getByRole("button", { name: "Actions sur le projet" }),
    );

    expect(
      screen.queryByRole("button", { name: /Déclarer un sous-projet/ }),
    ).toBeNull();
  });
});

describe("ProjectTabs, read by a guest", () => {
  it("offers none of the gestures the menu folds", () => {
    // Declaring, attaching, archiving, deleting: every entry of the menu
    // writes, so the menu goes whole rather than opening on four refusals.
    mayWrite.value = false;
    tabs({ is_deletable: true, consumed_days: 0 });

    expect(screen.queryByRole("button", { name: "Actions sur le projet" })).toBeNull();
    mayWrite.value = true;
  });

  it("still opens every tab: a guest reads the mission whole", () => {
    mayWrite.value = false;
    tabs({ is_deletable: true, consumed_days: 0 });

    for (const tab of [
      "Pilotage",
      "Mises à jour",
      "Fichiers",
      "Catalogue",
      "Journal",
    ]) {
      expect(screen.getByRole("tab", { name: tab })).toBeInTheDocument();
    }
    mayWrite.value = true;
  });
});
