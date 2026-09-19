import { describe, expect, it, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import { MissionCard } from "./MissionCard";
import type { ProjectListItemResponse } from "@/lib/api/generated/model";
import type { HomeMission } from "@/lib/home";

const mission = (overrides: Partial<HomeMission> = {}): HomeMission => ({
  item: {
    project: {
      id: 1,
      label: "Portail bailleurs",
      kind: "project",
      status: "development",
      priority: "high",
      parent_id: null,
      is_active: true,
    },
  } as ProjectListItemResponse,
  days: 6,
  isContributor: true,
  parentLabel: null,
  ...overrides,
});

describe("MissionCard", () => {
  it("names the project, its phase and its urgency", () => {
    render(<MissionCard mission={mission()} onOpen={vi.fn()} />);

    expect(
      screen.getByRole("button", { name: "Portail bailleurs" }),
    ).toBeInTheDocument();
    expect(screen.getByText("Réalisation")).toBeInTheDocument();
    expect(screen.getByText("Haute")).toBeInTheDocument();
  });

  it("says what was put on it this month", () => {
    render(<MissionCard mission={mission({ days: 4.5 })} onOpen={vi.fn()} />);

    expect(screen.getByText(/4,5 j/)).toBeInTheDocument();
  });

  it("says nothing was entered rather than leaving the figure blank", () => {
    // A card with no figure reads as a card whose figure failed to load.
    render(<MissionCard mission={mission({ days: 0 })} onOpen={vi.fn()} />);

    expect(screen.getByText("Aucun temps saisi ce mois-ci")).toBeInTheDocument();
  });

  it("names what a work package hangs from", () => {
    render(
      <MissionCard
        mission={mission({ parentLabel: "Refonte extranet" })}
        onOpen={vi.fn()}
      />,
    );

    expect(screen.getByText("Refonte extranet")).toBeInTheDocument();
  });

  it("opens the project from its name, and only once", async () => {
    const onOpen = vi.fn();
    render(<MissionCard mission={mission()} onOpen={onOpen} />);

    await userEvent.click(screen.getByRole("button", { name: "Portail bailleurs" }));

    // The card carries a handler of its own: the name must not fire it twice.
    expect(onOpen).toHaveBeenCalledExactlyOnceWith(1);
  });
});
