import { describe, expect, it, vi } from "vitest";
import { fireEvent, render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import { ProjectSteeringTab } from "./ProjectSteeringTab";
import type {
  ProjectCategory,
  ProjectDetailResponse,
  ProjectKind,
} from "@/lib/api/generated/model";

// The pickers ask the server for the team; steering itself does not.
vi.mock("@/lib/api/queries", () => ({
  useTeammates: () => ({ teammates: [] }),
  useTags: () => ({ tags: [] }),
}));

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

const detail = (
  kind: ProjectKind,
  category: ProjectCategory | null = null,
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
      business_contacts: null,
      description: null,
      go_live_date: null,
    },
    departments: [],
    links: [],
    phases: [],
    leads: [],
    tech_leads: [],
    contributors: [],
    consumed_days: 0,
    contributions: [],
    sub_projects: [],
    tags: [],
  }) as unknown as ProjectDetailResponse;

const steering = (
  kind: ProjectKind,
  category: ProjectCategory | null = null,
  updateFields = vi.fn(),
) =>
  render(
    <ProjectSteeringTab
      detail={detail(kind, category)}
      onChange={vi.fn()}
      saveSheet={vi.fn()}
      changePhase={vi.fn()}
      updateFields={updateFields}
      addSubProject={vi.fn()}
      toggleFollow={vi.fn()}
      addTag={vi.fn()}
      removeTag={vi.fn()}
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

/**
 * Who is on the mission this week and who answers for its code are two
 * questions, and the sheet asks them one under the other rather than folding
 * them into one list.
 */
describe("who is on a mission", () => {
  it("asks for the people on it now and for the ones who answer for it", () => {
    steering("project");

    expect(
      screen.getByRole("button", { name: "Modifier les référents techniques" }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: "Modifier les intervenants actuels" }),
    ).toBeInTheDocument();
  });
});

describe("the day a mission goes live", () => {
  it("is posted from the sheet, under the phase", async () => {
    const updateFields = vi.fn();
    steering("project", null, updateFields);

    await userEvent.click(
      screen.getByRole("button", { name: "Date annoncée pour Portail" }),
    );
    const field = screen.getByLabelText("Date annoncée pour Portail");
    await userEvent.type(field, "2026-11-15");
    fireEvent.blur(field);

    expect(updateFields).toHaveBeenCalledWith({ go_live_date: "2026-11-15" });
  });
});

describe("following a mission from its sheet", () => {
  const followed = (kind: ProjectKind, isFollowed: boolean) => {
    const toggleFollow = vi.fn();
    const sheet = detail(kind);
    (sheet.project as { is_followed: boolean }).is_followed = isFollowed;
    render(
      <ProjectSteeringTab
        detail={sheet}
        onChange={vi.fn()}
        saveSheet={vi.fn()}
        changePhase={vi.fn()}
        updateFields={vi.fn()}
        addSubProject={vi.fn()}
        toggleFollow={toggleFollow}
        addTag={vi.fn()}
        removeTag={vi.fn()}
      />,
    );
    return toggleFollow;
  };

  it("raises the mark from the Informations section", async () => {
    const toggleFollow = followed("project", false);

    expect(screen.getByText("Non suivi")).toBeInTheDocument();
    await userEvent.click(screen.getByRole("button", { name: "Suivre ce projet" }));

    expect(toggleFollow).toHaveBeenCalledOnce();
  });

  it("lowers it on a followed mission", async () => {
    const toggleFollow = followed("work_package", true);

    expect(screen.getByText("Projet suivi")).toBeInTheDocument();
    await userEvent.click(
      screen.getByRole("button", { name: "Ne plus suivre ce projet" }),
    );

    expect(toggleFollow).toHaveBeenCalledOnce();
  });

  /** An absence is not something anybody keeps an eye on. */
  it("says nothing of it on off-project work", () => {
    followed("off_project", false);

    expect(screen.queryByText("Non suivi")).toBeNull();
  });
});

describe("the tags of a mission", () => {
  const tagged = (kind: ProjectKind, ...names: string[]) => ({
    ...detail(kind),
    tags: names.map((name, index) => ({ id: index + 1, name, color: "blue" })),
  });

  function sheet(
    over: ProjectDetailResponse | ReturnType<typeof tagged>,
    handlers = {},
  ) {
    const props = { addTag: vi.fn(), removeTag: vi.fn(), ...handlers };
    render(
      <ProjectSteeringTab
        detail={over as unknown as ProjectDetailResponse}
        onChange={vi.fn()}
        saveSheet={vi.fn()}
        changePhase={vi.fn()}
        updateFields={vi.fn()}
        addSubProject={vi.fn()}
        toggleFollow={vi.fn()}
        {...props}
      />,
    );
    return props;
  }

  it("names the tags the mission carries, under « Informations »", () => {
    sheet(tagged("project", "IA", "Chronopost"));

    expect(screen.getByText("Tags")).toBeInTheDocument();
    expect(screen.getByText("IA")).toBeInTheDocument();
    expect(screen.getByText("Chronopost")).toBeInTheDocument();
  });

  it("takes a tag off through the sheet's own gesture", async () => {
    const { removeTag } = sheet(tagged("project", "IA"));

    await userEvent.click(screen.getByRole("button", { name: "Retirer le tag IA" }));

    expect(removeTag).toHaveBeenCalledWith(1);
  });

  it("puts one on through the sheet's own gesture", async () => {
    const { addTag } = sheet(tagged("project"));

    await userEvent.click(screen.getByRole("button", { name: "Ajouter un tag" }));
    await userEvent.type(screen.getByLabelText("Rechercher un tag"), "Frigo{Enter}");

    expect(addTag).toHaveBeenCalledWith("Frigo");
  });

  it("is offered on a work package, which carries its own", () => {
    sheet(tagged("work_package"));

    expect(screen.getByRole("button", { name: "Ajouter un tag" })).toBeInTheDocument();
  });

  /** An absence has nothing to be found by: the server refuses it as well. */
  it("is not offered on off-project work", () => {
    sheet(tagged("off_project"));

    expect(screen.queryByText("Tags")).not.toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "Ajouter un tag" })).toBeNull();
  });
});
