import { describe, expect, it, vi } from "vitest";
import { render, screen, within } from "@testing-library/react";
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
 */
function renderInRow(ui: React.ReactElement) {
  return render(
    <table>
      <tbody>
        <tr>{ui}</tr>
      </tbody>
    </table>,
  );
}

describe("DayCell", () => {
  it("is a table cell, not a bare button in the row", () => {
    renderInRow(<DayCell {...baseProps} value={0} onChange={vi.fn()} />);

    const cell = screen.getByRole("cell");
    expect(cell.tagName).toBe("TD");
    expect(within(cell).getByRole("button")).toBeInTheDocument();
  });

  it("notifies the next value on click", async () => {
    const onChange = vi.fn();
    renderInRow(<DayCell {...baseProps} value={0} onChange={onChange} />);

    await userEvent.click(screen.getByRole("button"));

    expect(onChange).toHaveBeenCalledWith(1);
  });

  it("shows a half day readably", () => {
    renderInRow(<DayCell {...baseProps} value={0.5} onChange={vi.fn()} />);

    expect(screen.getByRole("button")).toHaveTextContent("½");
  });

  it("shows nothing when the cell is empty", () => {
    renderInRow(<DayCell {...baseProps} value={0} onChange={vi.fn()} />);

    expect(screen.getByRole("button")).toHaveTextContent("");
  });

  it("is not clickable when the month is locked", async () => {
    const onChange = vi.fn();
    render(<DayCell {...baseProps} value={1} isReadOnly onChange={onChange} />);

    await userEvent.click(screen.getByRole("button"));

    expect(onChange).not.toHaveBeenCalled();
  });

  it("locks a non-working day left empty", async () => {
    const onChange = vi.fn();
    renderInRow(<DayCell {...baseProps} value={0} isOffDay onChange={onChange} />);

    await userEvent.click(screen.getByRole("button"));

    expect(onChange).not.toHaveBeenCalled();
  });

  it("locks a non-working day even when it carries a value", async () => {
    const onChange = vi.fn();
    renderInRow(<DayCell {...baseProps} value={1} isOffDay onChange={onChange} />);

    await userEvent.click(screen.getByRole("button"));

    expect(onChange).not.toHaveBeenCalled();
  });

  it("carries an accessible label", () => {
    renderInRow(<DayCell {...baseProps} value={1} onChange={vi.fn()} />);

    expect(screen.getByRole("button", { name: "15 septembre" })).toBeInTheDocument();
  });
});

describe("DayCell, reached with the keys", () => {
  it("says which cell it is, so the grid can find it back", () => {
    renderInRow(<DayCell {...baseProps} value={0} onChange={vi.fn()} />);

    expect(screen.getByRole("button")).toHaveAttribute("data-cell", "10:2026-09-15");
  });

  it("stays out of the tab order unless it is the grid's stop", () => {
    const { rerender } = renderInRow(
      <DayCell {...baseProps} value={0} onChange={vi.fn()} />,
    );
    expect(screen.getByRole("button")).toHaveAttribute("tabindex", "-1");

    rerender(
      <table>
        <tbody>
          <tr>
            <DayCell {...baseProps} isTabStop value={0} onChange={vi.fn()} />
          </tr>
        </tbody>
      </table>,
    );
    expect(screen.getByRole("button")).toHaveAttribute("tabindex", "0");
  });
});
