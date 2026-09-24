import { describe, expect, it, vi } from "vitest";
import { fireEvent, render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import { TimesheetGrid } from "./TimesheetGrid";
import type { GridRowResponse, MonthGridResponse } from "@/lib/api/generated/model";

const TODAY = "2026-09-16";

function makeGrid(overrides: Partial<MonthGridResponse> = {}): MonthGridResponse {
  const days = [
    { day: "2026-09-14", kind: "working", label: null, is_off_day: false },
    { day: "2026-09-15", kind: "working", label: null, is_off_day: false },
    { day: "2026-09-16", kind: "working", label: null, is_off_day: false },
    { day: "2026-09-19", kind: "weekend", label: null, is_off_day: true },
    { day: "2026-09-25", kind: "working", label: null, is_off_day: false },
  ];
  return {
    user_id: 1,
    month: "2026-09-01",
    days,
    rows: [
      {
        project_id: 10,
        label: "Portail bailleurs",
        kind: "project",
        estimated_days: 20,
        values: { "2026-09-15": 1, "2026-09-25": 1 },
        actual_total: 1,
        forecast_total: 1,
        total: 2,
        total_consumed_days: 7,
      },
    ],
    day_totals: days.map((day) => ({
      day: day.day,
      total: day.day === "2026-09-15" ? 1 : day.day === "2026-09-25" ? 1 : 0,
      exceeds_capacity: false,
    })),
    working_days: 22,
    is_writable: true,
    actual_total: 1,
    forecast_total: 1,
    ...overrides,
  } as MonthGridResponse;
}

/** A mission put on the month, with nothing entered on it yet. */
const EMPTY_ROW: GridRowResponse = {
  project_id: 11,
  label: "Absences",
  kind: "off_project",
  estimated_days: null,
  values: {},
  actual_total: 0,
  forecast_total: 0,
  total: 0,
  total_consumed_days: 0,
} as GridRowResponse;

const baseProps = {
  today: TODAY,
  readOnly: false,
  onSetValue: vi.fn(),
};

describe("TimesheetGrid", () => {
  it("shows one row per mission", () => {
    render(<TimesheetGrid {...baseProps} grid={makeGrid()} />);

    expect(
      screen.getByRole("rowheader", { name: /Portail bailleurs/ }),
    ).toBeInTheDocument();
  });

  it("compares the project's consumption against its estimate, not the month's delivered days", () => {
    render(<TimesheetGrid {...baseProps} grid={makeGrid()} />);

    // The ratio lives in the mission's tooltip, which follows the cursor.
    fireEvent.mouseMove(screen.getByText("Portail bailleurs"), {
      clientX: 50,
      clientY: 80,
    });

    expect(screen.getByRole("tooltip")).toHaveTextContent("7/20 jrs. estimés");
  });

  it("notifies the next value when an empty cell is clicked", async () => {
    const onSetValue = vi.fn();
    render(<TimesheetGrid {...baseProps} grid={makeGrid()} onSetValue={onSetValue} />);

    await userEvent.click(
      screen.getByRole("button", { name: "Portail bailleurs — 2026-09-14" }),
    );

    expect(onSetValue).toHaveBeenCalledWith(10, "2026-09-14", 1);
  });

  it("cycles a full day to a half day", async () => {
    const onSetValue = vi.fn();
    render(<TimesheetGrid {...baseProps} grid={makeGrid()} onSetValue={onSetValue} />);

    await userEvent.click(
      screen.getByRole("button", { name: "Portail bailleurs — 2026-09-15" }),
    );

    expect(onSetValue).toHaveBeenCalledWith(10, "2026-09-15", 0.5);
  });

  it("shows a mission put on the month with nothing entered on it", () => {
    render(
      <TimesheetGrid
        {...baseProps}
        grid={makeGrid({ rows: [...makeGrid().rows, EMPTY_ROW] })}
      />,
    );

    expect(screen.getByRole("rowheader", { name: /Absences/ })).toBeInTheDocument();
  });

  it("locks every cell when the grid only reads", () => {
    render(<TimesheetGrid {...baseProps} readOnly grid={makeGrid()} />);

    const cells = screen.getAllByRole("button", { name: /Portail bailleurs/ });
    expect(cells.every((cell) => cell.hasAttribute("disabled"))).toBe(true);
  });

  it("shows a message when the month holds no mission", () => {
    render(<TimesheetGrid {...baseProps} grid={makeGrid({ rows: [] })} />);

    expect(screen.getByText(/Aucun projet pour ce mois/)).toBeInTheDocument();
  });

  /**
   * A validated month accepts nothing: inviting to add a mission there offers a
   * gesture the grid refuses.
   */
  it("states emptiness rather than inviting to add on a validated month", () => {
    render(<TimesheetGrid {...baseProps} readOnly grid={makeGrid({ rows: [] })} />);

    expect(
      screen.getByText(/Aucun projet n'a été déclaré sur ce mois/),
    ).toBeInTheDocument();
    expect(screen.queryByText(/Ajoutez-en un/)).toBeNull();
  });

  it("does not show that message as soon as a mission is there", () => {
    render(<TimesheetGrid {...baseProps} grid={makeGrid()} />);

    expect(screen.queryByText(/Aucun projet pour ce mois/)).toBeNull();
  });

  it("closes the table with a strong rule even with no mission", () => {
    render(<TimesheetGrid {...baseProps} grid={makeGrid({ rows: [] })} />);

    const cell = screen.getByText(/Aucun projet pour ce mois/);
    expect(cell.className).toContain("border-b-slate-500");
    expect(cell.className).toContain("border-r-slate-500");
  });

  it("keeps the add row in last place", () => {
    render(
      <TimesheetGrid
        {...baseProps}
        grid={makeGrid()}
        addingMission={<button>Ajouter un projet</button>}
      />,
    );

    const lines = screen.getAllByRole("row");
    expect(within(lines.at(-1)!).getByText("Ajouter un projet")).toBeInTheDocument();
  });

  it("lets the add row close the table with a strong rule", () => {
    render(
      <TimesheetGrid
        {...baseProps}
        grid={makeGrid()}
        addingMission={<button>Ajouter un projet</button>}
      />,
    );

    const lines = screen.getAllByRole("row");
    const cells = within(lines.at(-1)!).getAllByRole("rowheader");
    expect(cells[0].className).toContain("border-b-slate-500");
    // The mission before no longer closes anything: a light rule separates it.
    const mission = screen.getByRole("rowheader", { name: /Portail bailleurs/ });
    expect(mission.className).toContain("border-b-slate-300");
  });

  it("offers to add a mission rather than announcing emptiness", () => {
    render(
      <TimesheetGrid
        {...baseProps}
        grid={makeGrid({ rows: [] })}
        addingMission={<button>Ajouter un projet</button>}
      />,
    );

    expect(screen.queryByText(/Aucun projet pour ce mois/)).toBeNull();
    expect(screen.getByText("Ajouter un projet")).toBeInTheDocument();
  });

  it("offers to remove each mission, outside the table frame", () => {
    const onRemoveMission = vi.fn();
    render(
      <TimesheetGrid
        {...baseProps}
        grid={makeGrid()}
        onRemoveMission={onRemoveMission}
      />,
    );

    fireEvent.click(screen.getByRole("button", { name: "Retirer Portail bailleurs" }));

    expect(onRemoveMission).toHaveBeenCalledWith(10);
  });

  it("stops the top rule at the last data column", () => {
    render(
      <TimesheetGrid {...baseProps} grid={makeGrid()} onRemoveMission={vi.fn()} />,
    );

    const action = screen.getByText("Retirer le projet").closest("th")!;
    expect(action.className).not.toContain("border-t");
    // The totals column does carry it: the frame stops there.
    const totals = screen.getByText("Total du mois").closest("th")!;
    expect(totals.className).toContain("border-t-slate-500");
  });

  it("offers no removal when the grid only reads", () => {
    render(<TimesheetGrid {...baseProps} readOnly grid={makeGrid()} />);

    expect(screen.queryByRole("button", { name: /^Retirer/ })).toBeNull();
  });

  it("shrinks a weekend with no entry to a plain band", () => {
    render(<TimesheetGrid {...baseProps} grid={makeGrid()} />);

    const header = screen.getByRole("columnheader", { name: /S 19/ });
    expect(header.className).toContain("w-2.5");
  });

  it("keeps its width on a working day", () => {
    render(<TimesheetGrid {...baseProps} grid={makeGrid()} />);

    const header = screen.getByRole("columnheader", { name: /M 15/ });
    expect(header.className).toContain("w-9");
  });

  it("keeps its width on a weekend carrying an inherited entry", () => {
    // Data set before the ban must stay visible and correctable.
    const grid = makeGrid({
      days: [{ day: "2026-09-19", kind: "weekend", label: null, is_off_day: true }],
      day_totals: [{ day: "2026-09-19", total: 1, exceeds_capacity: false }],
      rows: [],
    } as Partial<MonthGridResponse>);
    render(<TimesheetGrid {...baseProps} grid={grid} />);

    const header = screen.getByRole("columnheader", { name: /S 19/ });
    expect(header.className).toContain("w-9");
    expect(header.className).not.toContain("w-2.5");
  });

  it("shows one total per day", () => {
    render(<TimesheetGrid {...baseProps} grid={makeGrid()} />);

    const footer = screen.getByRole("row", { name: /jrs\. ouvrés/ });
    expect(within(footer).getAllByRole("cell").at(-1)).toHaveTextContent("2");
  });

  it("puts the totals row right under the day header", () => {
    render(<TimesheetGrid {...baseProps} grid={makeGrid()} />);

    const rows = screen.getAllByRole("row");
    expect(rows[0]).toHaveTextContent("Projet");
    expect(rows[1]).toHaveTextContent("22 jrs. ouvrés");
    expect(rows[2]).toHaveTextContent("Portail bailleurs");
  });

  it("colours a full day green", () => {
    const grid = makeGrid({
      day_totals: [{ day: "2026-09-15", total: 1, exceeds_capacity: false }],
      days: [{ day: "2026-09-15", kind: "working", label: null, is_off_day: false }],
      rows: [],
    } as Partial<MonthGridResponse>);
    render(<TimesheetGrid {...baseProps} grid={grid} />);

    const totalRow = screen.getByRole("row", { name: /jrs\. ouvrés/ });
    expect(within(totalRow).getAllByRole("cell")[0].className).toContain(
      "bg-emerald-100",
    );
  });

  it("flags an incomplete day in the totals row", () => {
    const grid = makeGrid({
      day_totals: [{ day: "2026-09-15", total: 0.5, exceeds_capacity: false }],
      days: [{ day: "2026-09-15", kind: "working", label: null, is_off_day: false }],
      rows: [],
    } as Partial<MonthGridResponse>);
    render(<TimesheetGrid {...baseProps} grid={grid} />);

    const totalRow = screen.getByRole("row", { name: /jrs\. ouvrés/ });
    expect(within(totalRow).getAllByRole("cell")[0]).toHaveAttribute(
      "data-alert",
      "true",
    );
  });

  it("opens the mission panel when its label is clicked", async () => {
    const onOpenMission = vi.fn();
    render(
      <TimesheetGrid {...baseProps} grid={makeGrid()} onOpenMission={onOpenMission} />,
    );

    await userEvent.click(
      screen.getByRole("button", { name: "Ouvrir Portail bailleurs" }),
    );

    expect(onOpenMission).toHaveBeenCalledWith(10);
  });

  it("leaves the mission label plain when no panel can be opened", () => {
    render(<TimesheetGrid {...baseProps} grid={makeGrid()} />);

    expect(
      screen.queryByRole("button", { name: "Ouvrir Portail bailleurs" }),
    ).not.toBeInTheDocument();
  });
});

/**
 * Moving around with the keys.
 *
 * A month with a dozen missions on it is a few hundred cells: reaching one of
 * them with the mouse is most of what filling a month in costs. These tests
 * are on the grid rather than on the cell, because what is being asserted is
 * where the focus lands — which only the grid knows.
 */
describe("TimesheetGrid, moved around with the keys", () => {
  /** Two missions, so that moving down has somewhere to go. */
  const twoRows = () =>
    makeGrid({ rows: [...makeGrid().rows, EMPTY_ROW] } as Partial<MonthGridResponse>);

  function cell(label: string, day: string): HTMLElement {
    return screen.getByRole("button", { name: `${label} — ${day}` });
  }

  it("moves to the next day of the same mission", async () => {
    render(<TimesheetGrid {...baseProps} grid={makeGrid()} />);

    cell("Portail bailleurs", "2026-09-14").focus();
    await userEvent.keyboard("{ArrowRight}");

    expect(cell("Portail bailleurs", "2026-09-15")).toHaveFocus();
  });

  it("steps over a non-working day rather than stopping on it", async () => {
    render(<TimesheetGrid {...baseProps} grid={makeGrid()} />);

    cell("Portail bailleurs", "2026-09-16").focus();
    await userEvent.keyboard("{ArrowRight}");

    // 19/09 is a weekend: the focus carries on to the next working day.
    expect(cell("Portail bailleurs", "2026-09-25")).toHaveFocus();
  });

  it("moves to the same day of the mission below, and back up", async () => {
    render(<TimesheetGrid {...baseProps} grid={twoRows()} />);

    // The rows are drawn in alphabetical order: « Absences » sits above.
    cell("Absences", "2026-09-15").focus();
    await userEvent.keyboard("{ArrowDown}");
    expect(cell("Portail bailleurs", "2026-09-15")).toHaveFocus();

    await userEvent.keyboard("{ArrowUp}");
    expect(cell("Absences", "2026-09-15")).toHaveFocus();
  });

  it("stays put at the end of a row: the grid does not wrap", async () => {
    render(<TimesheetGrid {...baseProps} grid={makeGrid()} />);

    const last = cell("Portail bailleurs", "2026-09-25");
    last.focus();
    await userEvent.keyboard("{ArrowRight}");

    expect(last).toHaveFocus();
  });

  it("goes to the first and the last day of the row", async () => {
    render(<TimesheetGrid {...baseProps} grid={makeGrid()} />);

    cell("Portail bailleurs", "2026-09-15").focus();
    await userEvent.keyboard("{End}");
    expect(cell("Portail bailleurs", "2026-09-25")).toHaveFocus();

    await userEvent.keyboard("{Home}");
    expect(cell("Portail bailleurs", "2026-09-14")).toHaveFocus();
  });

  /**
   * One stop for the whole grid, as a grid widget has: tabbing through three
   * hundred cells to reach what is after them is not navigation.
   */
  it("holds a single tab stop, which follows the focus", async () => {
    render(<TimesheetGrid {...baseProps} grid={makeGrid()} />);

    const first = cell("Portail bailleurs", "2026-09-14");
    expect(first).toHaveAttribute("tabindex", "0");
    expect(cell("Portail bailleurs", "2026-09-15")).toHaveAttribute("tabindex", "-1");

    first.focus();
    await userEvent.keyboard("{ArrowRight}");

    expect(first).toHaveAttribute("tabindex", "-1");
    expect(cell("Portail bailleurs", "2026-09-15")).toHaveAttribute("tabindex", "0");
  });

  it("enters a value from the keyboard as a click would", async () => {
    const onSetValue = vi.fn();
    render(<TimesheetGrid {...baseProps} onSetValue={onSetValue} grid={makeGrid()} />);

    cell("Portail bailleurs", "2026-09-14").focus();
    await userEvent.keyboard(" ");

    expect(onSetValue).toHaveBeenCalledWith(10, "2026-09-14", 1);
  });
});

describe("TimesheetGrid, held inside its own scroller", () => {
  /**
   * A regression test on a class name, which is unusual — but the defect it
   * guards is a layout one, and jsdom computes no layout.
   *
   * The header cells carry `sr-only` labels, drawn `position: absolute`. With
   * no positioned ancestor they resolve against the document rather than the
   * table, escape the scroller, and stretch the page a couple of hundred
   * pixels to the right: reaching the end of a month then scrolled the whole
   * window sideways and took the sidebar off screen.
   */
  it("positions the table, so its screen-reader labels cannot escape it", () => {
    render(<TimesheetGrid {...baseProps} grid={makeGrid()} />);

    expect(screen.getByRole("table")).toHaveClass("relative");
  });
});
