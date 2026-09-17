import { describe, expect, it, vi } from "vitest";
import { fireEvent, render, screen, within } from "@testing-library/react";
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
        consomme_total_j: 7,
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
  extraRows: [],
  today: TODAY,
  onSetValue: vi.fn(),
};

describe("TimesheetGrid", () => {
  it("affiche une ligne par mission", () => {
    render(<TimesheetGrid {...baseProps} grid={makeGrid()} />);

    expect(
      screen.getByRole("rowheader", { name: /Portail bailleurs/ }),
    ).toBeInTheDocument();
  });

  it("compare le consommé du projet à son estimé, pas le réalisé du mois", () => {
    render(<TimesheetGrid {...baseProps} grid={makeGrid()} />);

    // Le ratio vit dans l'infobulle de la mission, qui suit le curseur.
    fireEvent.mouseMove(screen.getByText("Portail bailleurs"), {
      clientX: 50,
      clientY: 80,
    });

    expect(screen.getByRole("tooltip")).toHaveTextContent("7/20 jrs. estimés");
  });

  it("notifie la valeur suivante quand on clique une cellule vide", async () => {
    const onSetValue = vi.fn();
    render(<TimesheetGrid {...baseProps} grid={makeGrid()} onSetValue={onSetValue} />);

    await userEvent.click(
      screen.getByRole("button", { name: "Portail bailleurs — 2026-09-14" }),
    );

    expect(onSetValue).toHaveBeenCalledWith(10, "2026-09-14", 1);
  });

  it("fait tourner une journée pleine vers une demi-journée", async () => {
    const onSetValue = vi.fn();
    render(<TimesheetGrid {...baseProps} grid={makeGrid()} onSetValue={onSetValue} />);

    await userEvent.click(
      screen.getByRole("button", { name: "Portail bailleurs — 2026-09-15" }),
    );

    expect(onSetValue).toHaveBeenCalledWith(10, "2026-09-15", 0.5);
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

  it("affiche un message quand le mois ne contient aucune mission", () => {
    render(<TimesheetGrid {...baseProps} grid={makeGrid({ rows: [] })} />);

    expect(screen.getByText(/Aucune mission pour ce mois/)).toBeInTheDocument();
  });

  it("n'affiche pas ce message dès qu'une mission est présente", () => {
    render(<TimesheetGrid {...baseProps} grid={makeGrid()} />);

    expect(screen.queryByText(/Aucune mission pour ce mois/)).toBeNull();
  });

  it("ferme le tableau d'un trait fort même sans aucune mission", () => {
    render(<TimesheetGrid {...baseProps} grid={makeGrid({ rows: [] })} />);

    const cellule = screen.getByText(/Aucune mission pour ce mois/);
    expect(cellule.className).toContain("border-b-slate-500");
    expect(cellule.className).toContain("border-r-slate-500");
  });

  it("garde la ligne d'ajout en dernière position", () => {
    render(
      <TimesheetGrid
        {...baseProps}
        grid={makeGrid()}
        ajoutDeMission={<button>Ajouter une mission</button>}
      />,
    );

    const lignes = screen.getAllByRole("row");
    expect(within(lignes.at(-1)!).getByText("Ajouter une mission")).toBeInTheDocument();
  });

  it("laisse la ligne d'ajout fermer le tableau d'un trait fort", () => {
    render(
      <TimesheetGrid
        {...baseProps}
        grid={makeGrid()}
        ajoutDeMission={<button>Ajouter une mission</button>}
      />,
    );

    const lignes = screen.getAllByRole("row");
    const cellules = within(lignes.at(-1)!).getAllByRole("rowheader");
    expect(cellules[0].className).toContain("border-b-slate-500");
    // La mission qui precede ne ferme plus rien : un trait faible l'en separe.
    const mission = screen.getByRole("rowheader", { name: /Portail bailleurs/ });
    expect(mission.className).toContain("border-b-slate-300");
  });

  it("propose d'ajouter une mission plutôt que d'annoncer le vide", () => {
    render(
      <TimesheetGrid
        {...baseProps}
        grid={makeGrid({ rows: [] })}
        ajoutDeMission={<button>Ajouter une mission</button>}
      />,
    );

    expect(screen.queryByText(/Aucune mission pour ce mois/)).toBeNull();
    expect(screen.getByText("Ajouter une mission")).toBeInTheDocument();
  });

  it("réduit un week-end sans saisie à une simple bande", () => {
    render(<TimesheetGrid {...baseProps} grid={makeGrid()} />);

    const entete = screen.getByRole("columnheader", { name: /S 19/ });
    expect(entete.className).toContain("w-2.5");
  });

  it("garde sa largeur à un jour ouvré", () => {
    render(<TimesheetGrid {...baseProps} grid={makeGrid()} />);

    const entete = screen.getByRole("columnheader", { name: /M 15/ });
    expect(entete.className).toContain("w-9");
  });

  it("garde sa largeur à un week-end portant une saisie héritée", () => {
    // Une donnee posee avant l'interdiction doit rester visible et corrigeable.
    const grid = makeGrid({
      days: [{ jour: "2026-09-19", kind: "weekend", label: null, is_off_day: true }],
      day_totals: [{ jour: "2026-09-19", total: 1, exceeds_capacity: false }],
      rows: [],
    } as Partial<MonthGridResponse>);
    render(<TimesheetGrid {...baseProps} grid={grid} />);

    const entete = screen.getByRole("columnheader", { name: /S 19/ });
    expect(entete.className).toContain("w-9");
    expect(entete.className).not.toContain("w-2.5");
  });

  it("affiche un total par jour", () => {
    render(<TimesheetGrid {...baseProps} grid={makeGrid()} />);

    const footer = screen.getByRole("row", { name: /jrs\. ouvrés/ });
    expect(within(footer).getAllByRole("cell").at(-1)).toHaveTextContent("2");
  });

  it("place la ligne des totaux juste sous l'en-tête des jours", () => {
    render(<TimesheetGrid {...baseProps} grid={makeGrid()} />);

    const rows = screen.getAllByRole("row");
    expect(rows[0]).toHaveTextContent("Mission");
    expect(rows[1]).toHaveTextContent("22 jrs. ouvrés");
    expect(rows[2]).toHaveTextContent("Portail bailleurs");
  });

  it("colore en vert une journée complète", () => {
    const grid = makeGrid({
      day_totals: [{ jour: "2026-09-15", total: 1, exceeds_capacity: false }],
      days: [{ jour: "2026-09-15", kind: "ouvre", label: null, is_off_day: false }],
      rows: [],
    } as Partial<MonthGridResponse>);
    render(<TimesheetGrid {...baseProps} grid={grid} />);

    const totalRow = screen.getByRole("row", { name: /jrs\. ouvrés/ });
    expect(within(totalRow).getAllByRole("cell")[0].className).toContain(
      "bg-emerald-100",
    );
  });

  it("signale une journée incomplète dans la ligne des totaux", () => {
    const grid = makeGrid({
      day_totals: [{ jour: "2026-09-15", total: 0.5, exceeds_capacity: false }],
      days: [{ jour: "2026-09-15", kind: "ouvre", label: null, is_off_day: false }],
      rows: [],
    } as Partial<MonthGridResponse>);
    render(<TimesheetGrid {...baseProps} grid={grid} />);

    const totalRow = screen.getByRole("row", { name: /jrs\. ouvrés/ });
    expect(within(totalRow).getAllByRole("cell")[0]).toHaveAttribute(
      "data-alert",
      "true",
    );
  });
});
