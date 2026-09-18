import { describe, expect, it, vi } from "vitest";
import { fireEvent, render, screen } from "@testing-library/react";

import { ProjectCard } from "./ProjectCard";
import type { BoardCardResponse } from "@/lib/api/generated/model";

/** Frozen reference time: « il y a 2 h » must stay stable between runs. */
const NOW = new Date("2026-09-16T11:00:00Z");

const card = (over: Record<string, unknown> = {}): BoardCardResponse =>
  ({
    consumed_days: 5,
    build_days: 5,
    contributors: [{ id: 1, display_name: "Léa Chen", initials: "LC" }],
    comments: 0,
    latest_update: null,
    sub_projects: 0,
    parent: null,
    ...over,
    project: {
      id: 1,
      label: "Portail bailleurs",
      kind: "project",
      status: "development",
      parent_id: null,
      is_active: true,
      estimated_days: 20,
      category: "innovate_differentiate",
      go_live_date: "2026-11-15",
      position: 0,
      monday_item_id: null,
      monday_subitem_id: null,
      is_syncable_to_monday: false,
      is_deletable: false,
      ...(over.project as object),
    },
  }) as BoardCardResponse;

describe("ProjectCard", () => {
  it("shows the mission name", () => {
    render(<ProjectCard now={NOW} card={card()} />);

    expect(screen.getByRole("heading")).toHaveTextContent("Portail bailleurs");
  });

  it("compares the build against the estimate", () => {
    render(<ProjectCard now={NOW} card={card()} />);

    expect(screen.getByText("5/20 jrs. estimés")).toBeInTheDocument();
  });

  it("writes half days in decimal rather than as a fraction", () => {
    render(<ProjectCard now={NOW} card={card({ build_days: 7.5 })} />);

    expect(screen.getByText("7,5/20 jrs. estimés")).toBeInTheDocument();
  });

  it("settles for consumption when no estimate exists", () => {
    render(
      <ProjectCard now={NOW} card={card({ project: { estimated_days: null } })} />,
    );

    expect(screen.getByText("5 jrs. consommés")).toBeInTheDocument();
  });

  it("does not burden the card with the go-live date", () => {
    render(<ProjectCard now={NOW} card={card()} />);

    expect(screen.queryByText(/Mise en service/)).toBeNull();
  });

  it("shows the contributors", () => {
    render(<ProjectCard now={NOW} card={card()} />);

    expect(screen.getByText("LC")).toBeInTheDocument();
  });

  it("flags going over the budget", () => {
    render(<ProjectCard now={NOW} card={card({ build_days: 25 })} />);

    expect(screen.getByText("25/20 jrs. estimés").className).toContain("text-red-700");
  });

  it("warns as the budget draws near", () => {
    render(<ProjectCard now={NOW} card={card({ build_days: 17 })} />);

    expect(screen.getByText("17/20 jrs. estimés").className).toContain(
      "text-amber-700",
    );
  });

  it("stays quiet far from the budget", () => {
    render(<ProjectCard now={NOW} card={card({ build_days: 3 })} />);

    expect(screen.getByText("3/20 jrs. estimés").className).not.toContain(
      "text-red-700",
    );
  });
});

describe("what the card does not say", () => {
  // The board is there to steer: where a mission stands, what it has cost, who
  // looks after it. Urgency and strategic axis read in the sheet and in the
  // reference list, which are made for comparing.
  it("leaves urgency and axis off the card", () => {
    render(
      <ProjectCard now={NOW} card={card({ project: { priority: "critical" } })} />,
    );

    expect(screen.queryByText("Critique")).toBeNull();
    expect(screen.queryByText("Innover & différencier")).toBeNull();
  });
});

describe("an archived mission", () => {
  it("flags itself at a glance", () => {
    render(<ProjectCard now={NOW} card={card({ project: { is_active: false } })} />);

    expect(screen.getByText("Archivée")).toBeInTheDocument();
  });

  it("marks nothing on an active mission", () => {
    render(<ProjectCard now={NOW} card={card()} />);

    expect(screen.queryByText("Archivée")).toBeNull();
  });
});

describe("what the card carries in its footer", () => {
  it("counts the follow-up thread's comments", () => {
    render(<ProjectCard now={NOW} card={card({ comments: 2 })} />);

    expect(screen.getByLabelText("2 commentaires")).toHaveTextContent("2");
  });

  it("agrees the label in the singular", () => {
    render(<ProjectCard now={NOW} card={card({ comments: 1 })} />);

    expect(screen.getByLabelText("1 commentaire")).toBeInTheDocument();
  });

  it("counts the sub-projects", () => {
    render(<ProjectCard now={NOW} card={card({ sub_projects: 11 })} />);

    expect(screen.getByLabelText("11 sous-projets")).toHaveTextContent("11");
  });

  it("keeps the markers without counting anything when the mission is bare", () => {
    // Monday leaves the icons in place, with no number: the card keeps its
    // shape from one mission to the next, and absence reads as fast as a total.
    render(<ProjectCard now={NOW} card={card()} />);

    expect(screen.getByLabelText("Aucun commentaire")).toHaveTextContent("");
    expect(screen.getByLabelText("Aucun sous-projet")).toHaveTextContent("");
  });
});

describe("attachment to a parent project", () => {
  it("names the project the sub-project belongs to", () => {
    render(
      <ProjectCard
        now={NOW}
        card={card({ parent: { id: 7, label: "Refonte du SI" } })}
      />,
    );

    expect(screen.getByText("Refonte du SI")).toBeInTheDocument();
  });

  it("opens the parent without opening the mission itself", () => {
    const onOpen = vi.fn();
    render(
      <ProjectCard
        now={NOW}
        card={card({ parent: { id: 7, label: "Refonte du SI" } })}
        onOpen={onOpen}
      />,
    );

    fireEvent.click(screen.getByRole("button", { name: "Refonte du SI" }));

    expect(onOpen).toHaveBeenCalledTimes(1);
    expect(onOpen).toHaveBeenCalledWith(7);
  });

  it("shows no parent for a root project", () => {
    render(<ProjectCard now={NOW} card={card()} />);

    expect(screen.queryByText(/↳/)).toBeNull();
  });

  it("freezes the link during the drag", () => {
    // The copy following the cursor stands for a gesture under way: a
    // clickable link on it would have no target.
    render(
      <ProjectCard
        now={NOW}
        card={card({ parent: { id: 7, label: "Refonte du SI" } })}
        onOpen={vi.fn()}
        isDragging
      />,
    );

    expect(screen.queryByRole("button", { name: "Refonte du SI" })).toBeNull();
    expect(screen.getByText("Refonte du SI")).toBeInTheDocument();
  });
});

describe("opening the mission", () => {
  it("opens the mission on a click anywhere on the card", () => {
    const onOpen = vi.fn();
    render(<ProjectCard now={NOW} card={card()} onOpen={onOpen} />);

    fireEvent.click(screen.getByText("5/20 jrs. estimés"));

    expect(onOpen).toHaveBeenCalledWith(1);
  });

  it("opens from the title too, reachable by keyboard", () => {
    const onOpen = vi.fn();
    render(<ProjectCard now={NOW} card={card()} onOpen={onOpen} />);

    fireEvent.click(screen.getByRole("button", { name: "Portail bailleurs" }));

    expect(onOpen).toHaveBeenCalledTimes(1);
  });

  it("leaves their click to the controls the card carries", () => {
    // The drag handle and the contributor avatars must not open the mission
    // under the finger of whoever was aiming at them.
    const onOpen = vi.fn();
    render(
      <ProjectCard
        now={NOW}
        card={card()}
        onOpen={onOpen}
        handle={<button aria-label="Déplacer">glisser</button>}
      />,
    );

    fireEvent.click(screen.getByRole("button", { name: "Déplacer" }));

    expect(onOpen).not.toHaveBeenCalled();
  });

  it("shows no handle when the card does not move", () => {
    const { rerender } = render(<ProjectCard now={NOW} card={card()} />);
    expect(document.querySelector("svg.lucide-grip-vertical")).not.toBeNull();

    rerender(<ProjectCard now={NOW} card={card()} handle={null} />);

    expect(document.querySelector("svg.lucide-grip-vertical")).toBeNull();
  });

  it("opens nothing while the card follows the cursor", () => {
    // The copy following the mouse stands for a gesture under way, not a target.
    const onOpen = vi.fn();
    render(<ProjectCard now={NOW} card={card()} onOpen={onOpen} isDragging />);

    fireEvent.click(screen.getByText("5/20 jrs. estimés"));

    expect(onOpen).not.toHaveBeenCalled();
  });

  it("shows the latest message when hovering the comment count", () => {
    render(
      <ProjectCard
        now={NOW}
        card={card({
          comments: 2,
          latest_update: {
            author: { id: 1, display_name: "J. Buget", initials: "JB" },
            body: "Le cadrage commence lundi",
            published_at: "2026-09-16T09:00:00Z",
          },
        })}
      />,
    );

    fireEvent.mouseMove(screen.getByLabelText("2 commentaires"));

    const apercu = screen.getByRole("tooltip");
    expect(apercu).toHaveTextContent("J. Buget");
    expect(apercu).toHaveTextContent("il y a 2 h");
    expect(apercu).toHaveTextContent("Le cadrage commence lundi");
  });

  it("shows no preview when the thread is empty", () => {
    render(<ProjectCard now={NOW} card={card({ comments: 0 })} />);

    fireEvent.mouseMove(screen.getByLabelText("Aucun commentaire"));

    expect(screen.queryByRole("tooltip")).not.toBeInTheDocument();
  });
});
