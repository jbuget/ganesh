import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/react";

import { DayTotalCell } from "./DayTotalCell";

const base = { isOffDay: false };

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
  it("shows a full day in green", () => {
    expect(renderCell({ value: 1 }).className).toContain("bg-emerald-100");
  });

  it("flags an incomplete day", () => {
    expect(renderCell({ value: 0.5 })).toHaveAttribute("data-alert", "true");
  });

  it("flags a day gone over", () => {
    expect(renderCell({ value: 1.5 })).toHaveAttribute("data-alert", "true");
  });

  it("flags nothing for a full day", () => {
    expect(renderCell({ value: 1 })).not.toHaveAttribute("data-alert");
  });

  it("leaves an empty day blank", () => {
    expect(renderCell({ value: 0 }).className).toContain("bg-white");
  });

  it("greys a non-working day with no entry", () => {
    expect(renderCell({ value: 0, isOffDay: true }).className).toContain(
      "bg-slate-100",
    );
  });

  it("the value wins over a non-working day", () => {
    expect(renderCell({ value: 1, isOffDay: true }).className).toContain(
      "bg-emerald-100",
    );
  });
});
