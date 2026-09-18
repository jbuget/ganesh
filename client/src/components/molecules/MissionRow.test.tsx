import { describe, expect, it, vi } from "vitest";
import { fireEvent, render, screen } from "@testing-library/react";

import { MissionRow } from "./MissionRow";
import type { ProjectListItemResponse } from "@/lib/api/generated/model";

const NOW = new Date("2026-09-17T12:00:00Z");

const member = (id: number, name: string) => ({
  id,
  display_name: name,
  initials: name.slice(0, 2).toUpperCase(),
});

const mission = (fields: Record<string, unknown> = {}): ProjectListItemResponse =>
  ({
    project: {
      id: 1,
      label: "Portail",
      kind: "project",
      status: "development",
      category: "automate_streamline",
      estimated_days: 12,
      parent_id: null,
      is_active: true,
      ...fields,
    },
    leads: [],
    contributors: [],
    delivered_days: 0,
    comments: 0,
    latest_update: null,
  }) as unknown as ProjectListItemResponse;

function line(content: React.ReactNode) {
  return render(
    <table>
      <tbody>{content}</tbody>
    </table>,
  );
}

describe("MissionRow", () => {
  it("shows the phase, the category and the estimate", () => {
    line(
      <MissionRow
        mission={mission()}
        now={NOW}
        onOpen={() => {}}
        onOpenThread={() => {}}
      />,
    );

    expect(screen.getByText("Réalisation")).toBeInTheDocument();
    expect(screen.getByText("Automatiser & fluidifier")).toBeInTheDocument();
    expect(screen.getByText("12 jrs.")).toBeInTheDocument();
  });

  it("carries the declared priority", () => {
    line(
      <MissionRow
        mission={mission({ priority: "critical" })}
        now={NOW}
        onOpen={() => {}}
        onOpenThread={() => {}}
      />,
    );

    expect(screen.getByText("Critique")).toBeInTheDocument();
  });

  it("leaves the column empty when the mission is not placed", () => {
    line(
      <MissionRow
        mission={mission({ priority: null })}
        now={NOW}
        onOpen={() => {}}
        onOpenThread={() => {}}
      />,
    );

    ["Critique", "Haute", "Normale", "Basse"].forEach((urgency) => {
      expect(screen.queryByText(urgency)).toBeNull();
    });
  });

  it("shows delivered beside estimated", () => {
    const consommee = {
      ...mission(),
      delivered_days: 4.5,
    } as ProjectListItemResponse;

    line(
      <MissionRow
        mission={consommee}
        now={NOW}
        onOpen={() => {}}
        onOpenThread={() => {}}
      />,
    );

    expect(screen.getByText("4.5 jrs.")).toBeInTheDocument();
  });

  it("leaves delivered empty while nothing is declared", () => {
    line(
      <MissionRow
        mission={mission()}
        now={NOW}
        onOpen={() => {}}
        onOpenThread={() => {}}
      />,
    );

    expect(screen.getAllByText(/jrs\./)).toHaveLength(1);
  });

  it("carries the count of its mission's follow-up thread", () => {
    const suivie = { ...mission(), comments: 3 } as ProjectListItemResponse;

    line(
      <MissionRow
        mission={suivie}
        now={NOW}
        onOpen={() => {}}
        onOpenThread={() => {}}
      />,
    );

    expect(screen.getByLabelText("3 mises à jour")).toHaveTextContent("3");
  });

  it("shows on hover the latest message, signed, dated and formatted", () => {
    const suivie = {
      ...mission(),
      comments: 2,
      latest_update: {
        author: { id: 1, display_name: "Léa Chen", initials: "LÉ" },
        body: "La **recette** commence lundi",
        published_at: "2026-09-17T09:00:00Z",
      },
    } as ProjectListItemResponse;

    line(
      <MissionRow
        mission={suivie}
        now={NOW}
        onOpen={() => {}}
        onOpenThread={() => {}}
      />,
    );
    fireEvent.mouseMove(screen.getByLabelText("2 mises à jour"));

    const infobulle = screen.getByRole("tooltip");
    expect(infobulle).toHaveTextContent("Léa Chen");
    expect(infobulle).toHaveTextContent("il y a 3 h");
    expect(infobulle).toHaveTextContent("La recette commence lundi");
    expect(infobulle.querySelector("strong")).toHaveTextContent("recette");
  });

  it("gives the message in full, without truncating it", () => {
    const long = `${"mot ".repeat(200)}fin`;
    const suivie = {
      ...mission(),
      comments: 1,
      latest_update: {
        author: { id: 1, display_name: "Léa Chen", initials: "LÉ" },
        body: long,
        published_at: "2026-09-17T09:00:00Z",
      },
    } as ProjectListItemResponse;

    line(
      <MissionRow
        mission={suivie}
        now={NOW}
        onOpen={() => {}}
        onOpenThread={() => {}}
      />,
    );
    fireEvent.mouseMove(screen.getByLabelText("1 mise à jour"));

    expect(screen.getByRole("tooltip")).toHaveTextContent("fin");
  });

  it("opens the mission's thread on a click on its count", () => {
    const openThread = vi.fn();
    const open = vi.fn();
    const suivie = { ...mission(), comments: 2 } as ProjectListItemResponse;

    line(
      <MissionRow mission={suivie} now={NOW} onOpen={open} onOpenThread={openThread} />,
    );
    fireEvent.click(screen.getByLabelText("2 mises à jour"));

    expect(openThread).toHaveBeenCalledTimes(1);
    // The whole row opens the mission: the counter must not do both.
    expect(open).not.toHaveBeenCalled();
  });

  it("shows nothing while the thread is empty", () => {
    line(
      <MissionRow
        mission={mission()}
        now={NOW}
        onOpen={() => {}}
        onOpenThread={() => {}}
      />,
    );

    expect(screen.queryByLabelText(/mise/)).not.toBeInTheDocument();
  });

  it("opens the mission on a click on its name", () => {
    const open = vi.fn();
    line(
      <MissionRow
        mission={mission()}
        now={NOW}
        onOpen={open}
        onOpenThread={() => {}}
      />,
    );

    fireEvent.click(screen.getByRole("button", { name: "Portail" }));

    expect(open).toHaveBeenCalledTimes(1);
  });

  it("tells leads from contributors", () => {
    const withWorld = {
      ...mission(),
      leads: [member(1, "Léa Chen")],
      contributors: [member(2, "Nino Garo")],
    } as ProjectListItemResponse;

    line(
      <MissionRow
        mission={withWorld}
        now={NOW}
        onOpen={() => {}}
        onOpenThread={() => {}}
      />,
    );

    expect(screen.getByText("LÉ")).toBeInTheDocument();
    expect(screen.getByText("NI")).toBeInTheDocument();
  });

  it("leaves the columns empty rather than inventing a value", () => {
    line(
      <MissionRow
        mission={mission({ category: null, estimated_days: null })}
        now={NOW}
        onOpen={() => {}}
        onOpenThread={() => {}}
      />,
    );

    expect(screen.queryByText(/jrs\./)).not.toBeInTheDocument();
    expect(screen.getByText("Réalisation")).toBeInTheDocument();
  });

  it("visually ties a sub-project to its parent", () => {
    line(
      <MissionRow
        mission={mission()}
        isWorkPackage
        now={NOW}
        onOpen={() => {}}
        onOpenThread={() => {}}
      />,
    );

    expect(screen.getByText("\u2514")).toBeInTheDocument();
  });

  it("does not mark a first-level project", () => {
    line(
      <MissionRow
        mission={mission()}
        now={NOW}
        onOpen={() => {}}
        onOpenThread={() => {}}
      />,
    );

    expect(screen.queryByText("\u2514")).not.toBeInTheDocument();
  });

  it("offers to fold a project carrying sub-projects", () => {
    line(
      <MissionRow
        mission={mission()}
        workPackages={2}
        expanded
        now={NOW}
        onOpen={() => {}}
        onOpenThread={() => {}}
        onToggle={() => {}}
      />,
    );

    const toggle = screen.getByRole("button", {
      name: "Masquer les 2 sous-projets de Portail",
    });
    expect(toggle).toHaveAttribute("aria-expanded", "true");
  });

  it("offers to unfold a project whose sub-projects are hidden", () => {
    line(
      <MissionRow
        mission={mission()}
        workPackages={2}
        expanded={false}
        now={NOW}
        onOpen={() => {}}
        onOpenThread={() => {}}
        onToggle={() => {}}
      />,
    );

    const toggle = screen.getByRole("button", {
      name: "Afficher les 2 sous-projets de Portail",
    });
    expect(toggle).toHaveAttribute("aria-expanded", "false");
  });

  it("toggles the sub-projects without opening the mission", () => {
    const toggle = vi.fn();
    const open = vi.fn();

    line(
      <MissionRow
        mission={mission()}
        workPackages={1}
        expanded
        now={NOW}
        onOpen={open}
        onOpenThread={() => {}}
        onToggle={toggle}
      />,
    );
    fireEvent.click(
      screen.getByRole("button", { name: "Masquer le sous-projet de Portail" }),
    );

    expect(toggle).toHaveBeenCalledTimes(1);
    expect(open).not.toHaveBeenCalled();
  });

  it("offers no toggle to a project with no sub-project", () => {
    line(
      <MissionRow
        mission={mission()}
        now={NOW}
        onOpen={() => {}}
        onOpenThread={() => {}}
      />,
    );

    expect(
      screen.queryByRole("button", { name: /sous-projet/ }),
    ).not.toBeInTheDocument();
  });

  it("announces off-project work, which has no phase", () => {
    line(
      <MissionRow
        mission={mission({ kind: "off_project", status: null, estimated_days: null })}
        now={NOW}
        onOpen={() => {}}
        onOpenThread={() => {}}
      />,
    );

    expect(screen.queryByText("Réalisation")).not.toBeInTheDocument();
  });
});
