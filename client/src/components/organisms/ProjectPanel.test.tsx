import { describe, expect, it, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import { ProjectPanel } from "./ProjectPanel";

const detail = vi.hoisted(() => ({
  current: null as { project: { label: string }; parent: unknown } | null,
}));

vi.mock("@/lib/use-project-detail", () => ({
  useProjectDetail: () => ({
    detail: detail.current,
    notFound: false,
    rename: vi.fn(),
    reload: vi.fn(),
    saveSheet: vi.fn(),
    saveDescription: vi.fn(),
    changePhase: vi.fn(),
    updateFields: vi.fn(),
    addLink: vi.fn(),
    removeLink: vi.fn(),
    addSubProject: vi.fn(),
    archive: vi.fn(),
    unarchive: vi.fn(),
    remove: vi.fn(),
  }),
}));

/** The four facets have their own tests: the header is what is asked here. */
vi.mock("@/components/organisms/ProjectTabs", () => ({
  ProjectTabs: () => <div />,
}));

function panel(parent: { id: number; label: string } | null) {
  detail.current = {
    project: { label: parent ? "Lot 1 – API" : "Espace locataire" },
    parent,
  };
  const onOpenMission = vi.fn();
  render(
    <ProjectPanel
      projectId={12}
      onClose={vi.fn()}
      onMissionChanged={vi.fn()}
      onOpenMission={onOpenMission}
    />,
  );
  return { onOpenMission };
}

describe("ProjectPanel", () => {
  /**
   * Opened from a link or from the thread, « Lot 1 – API » gives no clue as to
   * which service it builds.
   */
  it("names the project a work package belongs to", () => {
    panel({ id: 7, label: "Espace locataire" });

    expect(screen.getByText("Espace locataire")).toBeInTheDocument();
    expect(screen.getByText("Sous-projet")).toBeInTheDocument();
  });

  it("says nothing of a parent on a project, which has none", () => {
    panel(null);

    expect(screen.queryByText("Sous-projet")).toBeNull();
  });

  it("swaps the panel for the project, rather than leaving the screen", async () => {
    const { onOpenMission } = panel({ id: 7, label: "Espace locataire" });

    await userEvent.click(screen.getByRole("button", { name: /Sous-projet/ }));

    expect(onOpenMission).toHaveBeenCalledWith(7);
  });
});
