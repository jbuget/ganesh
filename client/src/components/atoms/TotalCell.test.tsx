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
  it("ne signale rien pour un total normal", () => {
    renderInTable(<TotalCell value={1} />);

    expect(screen.getByRole("cell")).not.toHaveAttribute("data-alert");
  });

  it("affiche un total entier", () => {
    renderInTable(<TotalCell value={3} />);

    expect(screen.getByRole("cell")).toHaveTextContent("3");
  });

  it("affiche un total avec demi-journée", () => {
    renderInTable(<TotalCell value={3.5} />);

    expect(screen.getByRole("cell")).toHaveTextContent("3½");
  });

  it("reste vide quand rien n'est saisi", () => {
    renderInTable(<TotalCell value={0} />);

    expect(screen.getByRole("cell")).toHaveTextContent("");
  });

  it("signale visuellement un dépassement", () => {
    renderInTable(<TotalCell value={1.5} isAlert />);

    expect(screen.getByRole("cell")).toHaveAttribute("data-alert", "true");
  });
});
