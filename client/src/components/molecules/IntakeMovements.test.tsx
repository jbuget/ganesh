import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/react";

import { IntakeMovements } from "./IntakeMovements";

const INTAKE = {
  submitted: 6,
  accepted: 3,
  rejected: 1,
  deferred: 1,
  converted: 2,
  waiting: 2,
  oldest_wait_days: 10,
};

describe("IntakeMovements", () => {
  it("lines up what was asked, answered and built", () => {
    render(<IntakeMovements intake={INTAKE} />);

    for (const label of [
      "Déposés",
      "Acceptés",
      "Refusés",
      "Reportés",
      "Devenus des projets",
    ]) {
      expect(screen.getByRole("meter", { name: label })).toBeInTheDocument();
    }
  });

  it("says so in words when nothing moved", () => {
    render(
      <IntakeMovements
        intake={{
          ...INTAKE,
          submitted: 0,
          accepted: 0,
          rejected: 0,
          deferred: 0,
          converted: 0,
        }}
      />,
    );

    expect(
      screen.getByText("Aucun besoin déposé ni arbitré sur la période."),
    ).toBeInTheDocument();
  });
});
