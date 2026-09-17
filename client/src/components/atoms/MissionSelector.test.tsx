import { describe, expect, it, vi } from "vitest";
import { render, screen } from "@testing-library/react";

import { MissionSelector } from "./MissionSelector";
import type { ProjectResponse } from "@/lib/api/generated/model";

/**
 * Le menu deroulant repose sur Base UI, qui ne s'ouvre pas sous jsdom : son
 * contenu — champ de recherche compris — se verifie dans le navigateur. Le tri
 * des missions, lui, est teste directement dans `lib/missions.test.ts`.
 */
const PROJECTS: ProjectResponse[] = [
  {
    id: 1,
    label: "Portail bailleurs",
    kind: "projet",
    statut: "cadrage",
    parent_id: null,
    actif: true,
    estime_j: null,
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
  it("expose un sélecteur nommé", () => {
    render(<MissionSelector {...baseProps} />);

    expect(
      screen.getByRole("combobox", { name: "Ajouter une mission" }),
    ).toBeInTheDocument();
  });

  it("invite à ajouter une mission", () => {
    render(<MissionSelector {...baseProps} />);

    expect(screen.getByText(/Ajouter une mission/)).toBeInTheDocument();
  });

  it("est désactivé quand le mois est verrouillé", () => {
    render(<MissionSelector {...baseProps} disabled />);

    expect(screen.getByRole("combobox")).toBeDisabled();
  });
});
