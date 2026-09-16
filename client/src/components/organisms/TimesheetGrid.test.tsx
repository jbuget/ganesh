import { describe, expect, it, vi } from "vitest";
import { render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import { TimesheetGrid } from "./TimesheetGrid";
import type { MonthGridResponse, ProjectResponse } from "@/lib/api/generated/model";

const TODAY = "2026-09-16";

function makeGrid(overrides: Partial<MonthGridResponse> = {}): MonthGridResponse {
  const days = [
    { jour: "2026-09-14", kind: "ouvre", label: null, is_off_day: false },
    { jour: "2026-09-15", kind: "ouvre", label: null, is_off_day: false },
    { jour: "2026-09-16", kind: "ouvre", label: null, is_off_day: false },
    { jour: "2026-09-19", kind: "weekend", label: null, is_off_day: true },
    { jour: "2026-09-25", kind: "ouvre", label: null, is_off_day: false },
  ];
  return {
    user_id: 1,
    mois: "2026-09-01",
    days,
    rows: [
      {
        project_id: 10,
        label: "Portail bailleurs",
        kind: "projet",
        estime_j: 20,
        values: { "2026-09-15": 1, "2026-09-25": 1 },
        total_realise: 1,
        total_prevu: 1,
        total: 2,
      },
    ],
    day_totals: days.map((day) => ({
      jour: day.jour,
      total: day.jour === "2026-09-15" ? 1 : day.jour === "2026-09-25" ? 1 : 0,
      exceeds_capacity: false,
    })),
    working_days: 22,
    is_writable: true,
    total_realise: 1,
    total_prevu: 1,
    ...overrides,
  } as MonthGridResponse;
}

const PROJECTS: ProjectResponse[] = [
  {
    id: 11,
    label: "Absences",
    kind: "hors_projet",
    statut: null,
    parent_id: null,
    actif: true,
    estime_j: null,
    is_syncable_to_monday: false,
  } as ProjectResponse,
];

const baseProps = {
  projects: PROJECTS,
  extraRows: [],
  today: TODAY,
  onSetValue: vi.fn(),
  onAddMission: vi.fn(),
  onDeclareNew: vi.fn(),
};

describe("TimesheetGrid", () => {
  it("affiche une ligne par mission", () => {
    render(<TimesheetGrid {...baseProps} grid={makeGrid()} />);

    expect(
      screen.getByRole("rowheader", { name: /Portail bailleurs/ }),
    ).toBeInTheDocument();
  });

  it("affiche le consommé face à l'estimé", () => {
    render(<TimesheetGrid {...baseProps} grid={makeGrid()} />);

    expect(
      screen.getByRole("rowheader", { name: /Portail bailleurs/ }),
    ).toHaveTextContent("1/20 j");
  });

  it("notifie la valeur suivante quand on clique une cellule vide", async () => {
    const onSetValue = vi.fn();
    render(<TimesheetGrid {...baseProps} grid={makeGrid()} onSetValue={onSetValue} />);

    await userEvent.click(
      screen.getByRole("button", { name: "Portail bailleurs — 2026-09-14" }),
    );

    expect(onSetValue).toHaveBeenCalledWith(10, "2026-09-14", 0.5);
  });

  it("fait tourner une journée pleine vers vide", async () => {
    const onSetValue = vi.fn();
    render(<TimesheetGrid {...baseProps} grid={makeGrid()} onSetValue={onSetValue} />);

    await userEvent.click(
      screen.getByRole("button", { name: "Portail bailleurs — 2026-09-15" }),
    );

    expect(onSetValue).toHaveBeenCalledWith(10, "2026-09-15", 0);
  });

  it("garde une ligne ajoutée mais encore vide", () => {
    render(<TimesheetGrid {...baseProps} grid={makeGrid()} extraRows={PROJECTS} />);

    expect(screen.getByRole("rowheader", { name: /Absences/ })).toBeInTheDocument();
  });

  it("verrouille toutes les cellules quand le mois est validé", () => {
    render(<TimesheetGrid {...baseProps} grid={makeGrid({ is_writable: false })} />);

    const cells = screen.getAllByRole("button", { name: /Portail bailleurs/ });
    expect(cells.every((cell) => cell.hasAttribute("disabled"))).toBe(true);
  });

  it("retire le sélecteur de mission quand le mois est validé", () => {
    render(<TimesheetGrid {...baseProps} grid={makeGrid({ is_writable: false })} />);

    expect(screen.queryByRole("combobox")).toBeNull();
  });

  it("affiche un total par jour", () => {
    render(<TimesheetGrid {...baseProps} grid={makeGrid()} />);

    const footer = screen.getByRole("row", { name: /Total par jour/ });
    expect(within(footer).getAllByRole("cell").at(-1)).toHaveTextContent("2");
  });

  it("signale une saisie posée sur un jour non ouvré", () => {
    const grid = makeGrid({
      day_totals: [{ jour: "2026-09-19", total: 1, exceeds_capacity: false }],
      days: [{ jour: "2026-09-19", kind: "weekend", label: null, is_off_day: true }],
      rows: [],
    } as Partial<MonthGridResponse>);
    render(<TimesheetGrid {...baseProps} grid={grid} />);

    const footer = screen.getByRole("row", { name: /Total par jour/ });
    const weekendCell = within(footer).getAllByRole("cell")[0];
    expect(weekendCell).toHaveAttribute("data-alert", "true");
  });
});
