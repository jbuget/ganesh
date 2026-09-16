import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/react";

import { DayTotalCell } from "./DayTotalCell";

const base = { isOffDay: false, isToday: false };

function renderCell(props: Partial<React.ComponentProps<typeof DayTotalCell>>) {
  render(
    <table>
      <tbody>
        <tr>
          <DayTotalCell value={0} {...base} {...props} />
        </tr>
      </tbody>
    </table>,
  );
  return screen.getByRole("cell");
}

describe("DayTotalCell", () => {
  it("affiche une journée complète en vert", () => {
    expect(renderCell({ value: 1 }).className).toContain("bg-emerald-100");
  });

  it("signale une journée incomplète", () => {
    expect(renderCell({ value: 0.5 })).toHaveAttribute("data-alert", "true");
  });

  it("signale une journée en dépassement", () => {
    expect(renderCell({ value: 1.5 })).toHaveAttribute("data-alert", "true");
  });

  it("ne signale rien pour une journée complète", () => {
    expect(renderCell({ value: 1 })).not.toHaveAttribute("data-alert");
  });

  it("laisse une journée vide en blanc", () => {
    expect(renderCell({ value: 0 }).className).toContain("bg-white");
  });

  it("grise un jour non ouvré sans saisie", () => {
    expect(renderCell({ value: 0, isOffDay: true }).className).toContain(
      "bg-slate-100",
    );
  });

  it("met la colonne du jour en jaune quand elle est vide", () => {
    expect(renderCell({ value: 0, isToday: true }).className).toContain("bg-amber-100");
  });

  it("la valeur prime sur le repère du jour courant", () => {
    expect(renderCell({ value: 1, isToday: true }).className).toContain(
      "bg-emerald-100",
    );
  });

  it("la valeur prime sur un jour non ouvré", () => {
    expect(renderCell({ value: 1, isOffDay: true }).className).toContain(
      "bg-emerald-100",
    );
  });
});
