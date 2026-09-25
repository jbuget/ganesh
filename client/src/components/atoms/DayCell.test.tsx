import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import { DayCell } from "./DayCell";

const baseProps = {
  isOffDay: false,
  isFuture: false,
  isReadOnly: false,
  cellId: "10:2026-09-15",
  label: "15 septembre",
};

/**
 * DayCell lives in a table row. Rendering it outside that context would hide an
 * invalid HTML structure, which silently breaks React hydration.
 *
 * The table carries `role="grid"`, as the real one does: that is what makes
 * the cells `gridcell` rather than plain `cell`.
 */
function renderInRow(ui: React.ReactElement) {
  return render(
    <table role="grid">
      <tbody>
        <tr>{ui}</tr>
      </tbody>
    </table>,
  );
}

describe("DayCell", () => {
  it("is the cell itself, with nothing interactive inside it", () => {
    // The value is typed, not clicked, so there is no control here to press:
    // the cell takes the focus and the keys do the rest.
    renderInRow(<DayCell {...baseProps} value={0} />);

    const cell = screen.getByRole("gridcell");
    expect(cell.tagName).toBe("TD");
    expect(screen.queryByRole("button")).not.toBeInTheDocument();
  });

  /**
   * The gesture this replaced: a click used to cycle the value, which put an
   * 8 or a 16 in the cell every time somebody clicked one to type in it.
   */
  it("changes nothing when it is clicked: a click only moves the focus", async () => {
    renderInRow(<DayCell {...baseProps} value={0} />);

    const cell = screen.getByRole("gridcell");
    await userEvent.click(cell);

    expect(cell).toHaveTextContent("");
    expect(cell).toHaveFocus();
  });

  it("shows the hours a cell holds, not the fraction of a day", () => {
    // A day is entered two hours at a time, and « 4 » fits a 36px cell where
    // « 0,5 » does not. The value stored is still half a day.
    renderInRow(<DayCell {...baseProps} value={0.5} />);

    expect(screen.getByRole("gridcell")).toHaveTextContent("4");
  });

  it("shows a quarter of a day as two hours", () => {
    renderInRow(<DayCell {...baseProps} value={0.25} />);

    expect(screen.getByRole("gridcell")).toHaveTextContent("2");
  });

  it("shows nothing when the cell is empty", () => {
    renderInRow(<DayCell {...baseProps} value={0} />);

    expect(screen.getByRole("gridcell")).toHaveTextContent("");
  });

  it("carries an accessible label", () => {
    renderInRow(<DayCell {...baseProps} value={1} />);

    expect(screen.getByRole("gridcell", { name: "15 septembre" })).toBeInTheDocument();
  });
});

describe("DayCell, when it takes no entry", () => {
  /**
   * A locked cell is out of the tab order entirely, which is also what keeps
   * the keys off it: no focus, no key event, nothing to refuse.
   */
  it("cannot be focused when the month is validated", async () => {
    renderInRow(<DayCell {...baseProps} value={1} isReadOnly />);

    const cell = screen.getByRole("gridcell");
    expect(cell).not.toHaveAttribute("tabindex");
    await userEvent.click(cell);
    expect(cell).not.toHaveFocus();
  });

  it("cannot be focused on a non-working day", async () => {
    renderInRow(<DayCell {...baseProps} value={0} isOffDay />);

    const cell = screen.getByRole("gridcell");
    expect(cell).not.toHaveAttribute("tabindex");
    await userEvent.click(cell);
    expect(cell).not.toHaveFocus();
  });

  it("locks a non-working day even when it carries a value", () => {
    // Inherited data stays visible and must not be written over here.
    renderInRow(<DayCell {...baseProps} value={1} isOffDay />);

    expect(screen.getByRole("gridcell")).toHaveAttribute("aria-readonly", "true");
  });
});

describe("DayCell, reached with the keys", () => {
  it("says which cell it is, so the grid can find it back", () => {
    renderInRow(<DayCell {...baseProps} value={0} />);

    expect(screen.getByRole("gridcell")).toHaveAttribute("data-cell", "10:2026-09-15");
  });

  it("stays out of the tab order unless it is the grid's stop", () => {
    const { rerender } = renderInRow(<DayCell {...baseProps} value={0} />);
    expect(screen.getByRole("gridcell")).toHaveAttribute("tabindex", "-1");

    rerender(
      <table role="grid">
        <tbody>
          <tr>
            <DayCell {...baseProps} isTabStop value={0} />
          </tr>
        </tbody>
      </table>,
    );
    expect(screen.getByRole("gridcell")).toHaveAttribute("tabindex", "0");
  });
});
