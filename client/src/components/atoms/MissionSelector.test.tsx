import { describe, expect, it, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import { MissionSelector } from "./MissionSelector";
import type { ProjectResponse } from "@/lib/api/generated/model";

const project = (id: number, label: string, kind: string): ProjectResponse =>
  ({
    id,
    label,
    kind,
    statut: kind === "hors_projet" ? null : "cadrage",
    parent_id: null,
    actif: true,
    estime_j: null,
    is_syncable_to_monday: false,
  }) as ProjectResponse;

const PROJECTS = [
  project(1, "Portail bailleurs", "projet"),
  project(2, "Absences", "hors_projet"),
];

const baseProps = {
  projects: PROJECTS,
  excludedIds: [],
  onSelect: vi.fn(),
  onDeclareNew: vi.fn(),
  disabled: false,
};

describe("MissionSelector", () => {
  it("propose les missions disponibles", () => {
    render(<MissionSelector {...baseProps} />);

    expect(
      screen.getByRole("option", { name: "Portail bailleurs" }),
    ).toBeInTheDocument();
    expect(screen.getByRole("option", { name: "Absences" })).toBeInTheDocument();
  });

  it("masque les missions déjà présentes dans la matrice", () => {
    render(<MissionSelector {...baseProps} excludedIds={[1]} />);

    expect(screen.queryByRole("option", { name: "Portail bailleurs" })).toBeNull();
  });

  it("notifie la mission choisie", async () => {
    const onSelect = vi.fn();
    render(<MissionSelector {...baseProps} onSelect={onSelect} />);

    await userEvent.selectOptions(screen.getByRole("combobox"), "1");

    expect(onSelect).toHaveBeenCalledWith(1);
  });

  it("permet de déclarer un nouveau projet", async () => {
    const onDeclareNew = vi.fn();
    render(<MissionSelector {...baseProps} onDeclareNew={onDeclareNew} />);

    await userEvent.selectOptions(screen.getByRole("combobox"), "__new__");

    expect(onDeclareNew).toHaveBeenCalled();
  });

  it("est désactivé quand le mois est verrouillé", () => {
    render(<MissionSelector {...baseProps} disabled />);

    expect(screen.getByRole("combobox")).toBeDisabled();
  });
});
