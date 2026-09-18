import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/react";

import { TotalCell } from "./TotalCell";

function renderInTable(ui: React.ReactElement) {
  return render(
    <table>
      <tbody>
        <tr>{ui}</tr>
      </tbody>
    </table>,
  );
}

describe("TotalCell", () => {
  it("flags nothing for a normal total", () => {
    renderInTable(<TotalCell value={1} />);

    expect(screen.getByRole("cell")).not.toHaveAttribute("data-alert");
  });

  it("shows a whole total", () => {
    renderInTable(<TotalCell value={3} />);

    expect(screen.getByRole("cell")).toHaveTextContent("3");
  });

  it("writes a half day in decimal rather than as a fraction", () => {
    renderInTable(<TotalCell value={3.5} />);

    expect(screen.getByRole("cell")).toHaveTextContent("3,5");
  });

  it("reste vide quand rien n'est saisi", () => {
    renderInTable(<TotalCell value={0} />);

    expect(screen.getByRole("cell")).toHaveTextContent("");
  });

  it("visually flags an overrun", () => {
    renderInTable(<TotalCell value={1.5} isAlert />);

    expect(screen.getByRole("cell")).toHaveAttribute("data-alert", "true");
  });
});
