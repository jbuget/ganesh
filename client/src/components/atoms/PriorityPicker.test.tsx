import { describe, expect, it, vi } from "vitest";
import { fireEvent, render, screen } from "@testing-library/react";

import { PriorityPicker } from "./PriorityPicker";

describe("PriorityPicker", () => {
  it("invite à situer une mission qui ne l'est pas", () => {
    render(<PriorityPicker valeur={null} onChange={vi.fn()} />);

    expect(
      screen.getByRole("button", { name: "Changer la priorité" }),
    ).toHaveTextContent("Priorité");
  });

  it("affiche l'urgence déclarée", () => {
    render(<PriorityPicker valeur="haute" onChange={vi.fn()} />);

    expect(
      screen.getByRole("button", { name: "Changer la priorité" }),
    ).toHaveTextContent("Haute");
  });

  it("propose les quatre urgences, de la plus forte à la plus faible", () => {
    render(<PriorityPicker valeur={null} onChange={vi.fn()} />);

    fireEvent.click(screen.getByRole("button", { name: "Changer la priorité" }));

    const choix = screen
      .getAllByRole("button")
      .map((bouton) => bouton.textContent)
      .filter((texte) => texte && texte !== "Priorité");
    expect(choix).toEqual(["Critique", "Haute", "Normale", "Basse"]);
  });

  it("déclare l'urgence choisie", () => {
    const onChange = vi.fn();
    render(<PriorityPicker valeur={null} onChange={onChange} />);

    fireEvent.click(screen.getByRole("button", { name: "Changer la priorité" }));
    fireEvent.click(screen.getByRole("button", { name: "Critique" }));

    expect(onChange).toHaveBeenCalledWith("critique");
  });

  it("retire l'urgence quand on reclique dessus", () => {
    // C'est le seul moyen de revenir a « aucune priorite ».
    const onChange = vi.fn();
    render(<PriorityPicker valeur="basse" onChange={onChange} />);

    fireEvent.click(screen.getByRole("button", { name: "Changer la priorité" }));
    fireEvent.click(screen.getByRole("button", { name: "Basse" }));

    expect(onChange).toHaveBeenCalledWith(null);
  });
});
