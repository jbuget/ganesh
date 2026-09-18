import { describe, expect, it, vi } from "vitest";
import { render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import { DayCell } from "./DayCell";

const baseProps = {
  isOffDay: false,
  isFuture: false,
  isReadOnly: false,
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
  it("est une cellule de tableau, pas un bouton nu dans la ligne", () => {
    renderInRow(<DayCell {...baseProps} value={0} onChange={vi.fn()} />);

    const cell = screen.getByRole("cell");
    expect(cell.tagName).toBe("TD");
    expect(within(cell).getByRole("button")).toBeInTheDocument();
  });

  it("notifie la valeur suivante au clic", async () => {
    const onChange = vi.fn();
    renderInRow(<DayCell {...baseProps} value={0} onChange={onChange} />);

    await userEvent.click(screen.getByRole("button"));

    expect(onChange).toHaveBeenCalledWith(1);
  });

  it("affiche une demi-journée de façon lisible", () => {
    renderInRow(<DayCell {...baseProps} value={0.5} onChange={vi.fn()} />);

    expect(screen.getByRole("button")).toHaveTextContent("½");
  });

  it("n'affiche rien quand la cellule est vide", () => {
    renderInRow(<DayCell {...baseProps} value={0} onChange={vi.fn()} />);

    expect(screen.getByRole("button")).toHaveTextContent("");
  });

  it("n'est pas cliquable quand le mois est verrouillé", async () => {
    const onChange = vi.fn();
    render(<DayCell {...baseProps} value={1} isReadOnly onChange={onChange} />);

    await userEvent.click(screen.getByRole("button"));

    expect(onChange).not.toHaveBeenCalled();
  });

  it("verrouille un jour non ouvré resté vide", async () => {
    const onChange = vi.fn();
    renderInRow(<DayCell {...baseProps} value={0} isOffDay onChange={onChange} />);

    await userEvent.click(screen.getByRole("button"));

    expect(onChange).not.toHaveBeenCalled();
  });

  it("verrouille un jour non ouvré même s'il porte une valeur", async () => {
    const onChange = vi.fn();
    renderInRow(<DayCell {...baseProps} value={1} isOffDay onChange={onChange} />);

    await userEvent.click(screen.getByRole("button"));

    expect(onChange).not.toHaveBeenCalled();
  });

  it("porte un libellé accessible", () => {
    renderInRow(<DayCell {...baseProps} value={1} onChange={vi.fn()} />);

    expect(screen.getByRole("button", { name: "15 septembre" })).toBeInTheDocument();
  });
});
