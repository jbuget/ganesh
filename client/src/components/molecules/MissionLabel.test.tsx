import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/react";

import { MissionLabel } from "./MissionLabel";

describe("MissionLabel", () => {
  it("affiche le libellé de la mission", () => {
    render(<MissionLabel label="Portail bailleurs" consommeJ={3} estimeJ={20} />);

    expect(screen.getAllByText("Portail bailleurs").length).toBeGreaterThan(0);
  });

  it("place le consommé et l'estimé dans l'infobulle", () => {
    render(<MissionLabel label="Portail bailleurs" consommeJ={3} estimeJ={20} />);

    expect(screen.getByRole("tooltip")).toHaveTextContent("3/20 jrs. estimés");
  });

  it("redonne le nom complet dans l'infobulle, car il peut être tronqué", () => {
    render(
      <MissionLabel
        label="Automatisation du reporting de la direction financière"
        consommeJ={1.5}
        estimeJ={12}
      />,
    );

    expect(screen.getByRole("tooltip")).toHaveTextContent(
      "Automatisation du reporting de la direction financière",
    );
  });

  it("n'affiche aucun ratio pour une activité sans estimé", () => {
    render(<MissionLabel label="Absences" consommeJ={4} estimeJ={null} />);

    expect(screen.getByRole("tooltip")).not.toHaveTextContent("estimés");
  });

  it("affiche un consommé nul comme zéro", () => {
    render(<MissionLabel label="Support" consommeJ={0} estimeJ={5} />);

    expect(screen.getByRole("tooltip")).toHaveTextContent("0/5 jrs. estimés");
  });
});
