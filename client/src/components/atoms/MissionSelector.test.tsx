import { describe, expect, it, vi } from "vitest";
import { render, screen } from "@testing-library/react";

import { MissionSelector } from "./MissionSelector";
import type { ProjectResponse } from "@/lib/api/generated/model";

/**
 * The dropdown rests on Base UI, which does not open under jsdom: its content
 * — search field included — is checked in the browser. The sorting of missions
 * is tested directly in `lib/missions.test.ts`.
 */
const PROJECTS: ProjectResponse[] = [
  {
    id: 1,
    label: "Portail bailleurs",
    kind: "project",
    status: "scoping",
    parent_id: null,
    is_active: true,
    estimated_days: null,
    is_syncable_to_monday: false,
  } as ProjectResponse,
];

const baseProps = {
  projects: PROJECTS,
  excludedIds: [],
  onSelect: vi.fn(),
  onDeclareNew: vi.fn(),
};

describe("MissionSelector", () => {
  it("exposes a named picker", () => {
    render(<MissionSelector {...baseProps} />);

    expect(
      screen.getByRole("combobox", { name: "Ajouter une mission" }),
    ).toBeInTheDocument();
  });

  it("invites adding a mission", () => {
    render(<MissionSelector {...baseProps} />);

    expect(screen.getByText(/Ajouter une mission/)).toBeInTheDocument();
  });

  it("is disabled when the month is locked", () => {
    render(<MissionSelector {...baseProps} disabled />);

    expect(screen.getByRole("combobox")).toBeDisabled();
  });
});
