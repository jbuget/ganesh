import { describe, expect, it, vi } from "vitest";
import { render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import { ProjectSteeringTab } from "./ProjectSteeringTab";
import type {
  ProjectCategory,
  ProjectDetailResponse,
  ProjectKind,
} from "@/lib/api/generated/model";

// The pickers ask the server for the team; steering itself does not.
vi.mock("@/lib/api/queries", () => ({ useTeammates: () => ({ teammates: [] }) }));

// The sheet reads what the mission is cut into as soon as it opens. Left
// alone, the call reaches a relative URL that no test server answers — which
// passes on a machine where the API happens to be running, and nowhere else.
vi.mock("@/lib/use-project-activities", () => ({
  useProjectActivities: () => ({
    activities: [],
    isLoading: false,
    add: vi.fn(),
    change: vi.fn(),
    archive: vi.fn(),
    remove: vi.fn(),
    unarchive: vi.fn(),
  }),
}));

/** One reference day for the whole file, as the screens freeze their own. */
const TODAY = new Date("2026-09-25T10:00:00");

const detail = (
  kind: ProjectKind,
  category: ProjectCategory | null = null,
  over: Partial<ProjectDetailResponse> = {},
): ProjectDetailResponse =>
  ({
    project: {
      id: 10,
      label: "Portail",
      kind,
      status: "scoping",
      parent_id: kind === "work_package" ? 9 : null,
      is_active: true,
      estimated_days: null,
      category,
      priority: null,
      go_live_date: null,
      business_contacts: null,
      description: null,
      ...(over.project ?? {}),
    },
    departments: [],
    links: [],
    phases: [],
    leads: [],
    contributors: [],
    consumed_days: 0,
    contributions: [],
    sub_projects: [],
    ...over,
  }) as unknown as ProjectDetailResponse;

const steering = (
  kind: ProjectKind,
  category: ProjectCategory | null = null,
  over: Partial<ProjectDetailResponse> = {},
  updateFields = vi.fn(),
) =>
  render(
    <ProjectSteeringTab
      editable
      detail={detail(kind, category, over)}
      now={TODAY}
      onChange={vi.fn()}
      saveSheet={vi.fn()}
      changePhase={vi.fn()}
      updateFields={updateFields}
      addSubProject={vi.fn()}
    />,
  );

describe("ProjectSteeringTab", () => {
  it("carries the sub-projects of a project", () => {
    steering("project");

    expect(screen.getByText("Sous-projets")).toBeInTheDocument();
  });

  /**
   * The hierarchy stops at two levels, and off-project work carries nothing:
   * the server refuses both. Offering the section anyway would be offering a
   * move that comes back as an error.
   */
  it.each([["work_package"], ["off_project"]] as const)(
    "carries none on %s",
    (kind) => {
      steering(kind);

      expect(screen.queryByText("Sous-projets")).toBeNull();
    },
  );
});

describe("the strategic axis of a mission", () => {
  it("is chosen on a project", () => {
    steering("project");

    expect(
      screen.getByRole("button", { name: "Changer la catégorie" }),
    ).toBeInTheDocument();
  });

  /**
   * The axis qualifies the product, not a slice of it: a work package reads
   * the one its project carries, and changing it means changing the project's
   * — for the project and all its packages at once.
   */
  it("is read, not chosen, on a work package", () => {
    steering("work_package", "innovate_differentiate");

    expect(screen.queryByRole("button", { name: "Changer la catégorie" })).toBeNull();
    expect(screen.getByText("Innover & différencier")).toBeInTheDocument();
  });

  it("says on a work package where it is defined", () => {
    steering("work_package", "innovate_differentiate");

    expect(screen.getByRole("link", { name: "Définie sur le projet" })).toHaveAttribute(
      "href",
      "/projects/9",
    );
  });

  it("sends a work package to its project when the project has none", () => {
    steering("work_package");

    expect(screen.getByText("Aucune")).toBeInTheDocument();
    expect(
      screen.getByRole("link", { name: "À définir sur le projet" }),
    ).toHaveAttribute("href", "/projects/9");
  });
});

describe("the day a project is announced for", () => {
  it("is read on the sheet, in words", () => {
    steering("project", null, {
      project: { go_live_date: "2026-11-30" },
    } as Partial<ProjectDetailResponse>);

    expect(screen.getByText("30 nov. 2026")).toBeInTheDocument();
  });

  /**
   * The same reading as the reference list. A sheet that showed the day and
   * said nothing of it having gone by would be the one screen where a late
   * mission looks on time.
   */
  it("says when the day has gone by", () => {
    steering("project", null, {
      project: { go_live_date: "2026-06-30" },
    } as Partial<ProjectDetailResponse>);

    expect(screen.getByText("en retard")).toBeInTheDocument();
  });

  it("offers to date a project nobody has dated", () => {
    steering("project");

    expect(
      screen.getByRole("button", { name: /Date annoncée pour Portail/ }),
    ).toHaveTextContent("Dater");
  });

  it("is posted from the sheet", async () => {
    const updateFields = vi.fn();
    steering("project", null, {}, updateFields);

    await userEvent.click(
      screen.getByRole("button", { name: /Date annoncée pour Portail/ }),
    );
    await userEvent.type(
      screen.getByLabelText("Date annoncée pour Portail"),
      "2026-11-30",
    );
    await userEvent.tab();

    expect(updateFields).toHaveBeenCalledWith({ go_live_date: "2026-11-30" });
  });
});

describe("the phases a project has been through", () => {
  it("names each one with the day it was reached", () => {
    steering("project", null, {
      phases: [
        { status: "scoping", label: "Cadrage", reached_at: "2026-05-12" },
        { status: "development", label: "Développement", reached_at: "2026-06-01" },
      ],
    } as Partial<ProjectDetailResponse>);

    // Asserted through the days, which nothing else on the sheet carries:
    // the phase picker above and the activity button below both say
    // « Cadrage » and « Développement » for reasons of their own.
    const crossings = within(screen.getByRole("list", { name: "Étapes franchies" }));
    expect(crossings.getByText("Cadrage")).toBeInTheDocument();
    expect(crossings.getByText("le 12 mai 2026")).toBeInTheDocument();
    expect(crossings.getByText("Développement")).toBeInTheDocument();
    expect(crossings.getByText("le 1 juin 2026")).toBeInTheDocument();
  });

  /** Nothing is invented: a project the register never followed says so. */
  it("says so when nothing was ever recorded", () => {
    steering("project");

    expect(screen.getByText("Aucun passage enregistré")).toBeInTheDocument();
  });
});
