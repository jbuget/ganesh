import { describe, expect, it, vi } from "vitest";
import { fireEvent, render, screen } from "@testing-library/react";

import { PriorityPicker } from "./PriorityPicker";

describe("PriorityPicker", () => {
  it("invites placing a mission that is not placed", () => {
    render(<PriorityPicker value={null} onChange={vi.fn()} />);

    expect(
      screen.getByRole("button", { name: "Changer la priorité" }),
    ).toHaveTextContent("Priorité");
  });

  it("shows the declared urgency", () => {
    render(<PriorityPicker value="high" onChange={vi.fn()} />);

    expect(
      screen.getByRole("button", { name: "Changer la priorité" }),
    ).toHaveTextContent("Haute");
  });

  it("offers the four urgencies, from strongest to weakest", () => {
    render(<PriorityPicker value={null} onChange={vi.fn()} />);

    fireEvent.click(screen.getByRole("button", { name: "Changer la priorité" }));

    const choice = screen
      .getAllByRole("button")
      .map((bouton) => bouton.textContent)
      .filter((body) => body && body !== "Priorité");
    expect(choice).toEqual(["Critique", "Haute", "Normale", "Basse"]);
  });

  it("declares the chosen urgency", () => {
    const onChange = vi.fn();
    render(<PriorityPicker value={null} onChange={onChange} />);

    fireEvent.click(screen.getByRole("button", { name: "Changer la priorité" }));
    fireEvent.click(screen.getByRole("button", { name: "Critique" }));

    expect(onChange).toHaveBeenCalledWith("critical");
  });

  it("retire l'urgence quand on reclique dessus", () => {
    // C'est le seul moyen de revenir a « aucune priorite ».
    const onChange = vi.fn();
    render(<PriorityPicker value="low" onChange={onChange} />);

    fireEvent.click(screen.getByRole("button", { name: "Changer la priorité" }));
    fireEvent.click(screen.getByRole("button", { name: "Basse" }));

    expect(onChange).toHaveBeenCalledWith(null);
  });
});
