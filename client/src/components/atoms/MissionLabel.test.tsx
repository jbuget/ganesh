import { describe, expect, it } from "vitest";
import { fireEvent, render, screen } from "@testing-library/react";

import { MissionLabel } from "./MissionLabel";

function renderLabel(props: Partial<React.ComponentProps<typeof MissionLabel>> = {}) {
  render(
    <MissionLabel label="Portail bailleurs" consommeJ={3} estimeJ={20} {...props} />,
  );
  return screen.getByText(props.label ?? "Portail bailleurs").parentElement!;
}

function survoler(element: HTMLElement, x = 100, y = 200) {
  fireEvent.mouseMove(element, { clientX: x, clientY: y });
}

describe("MissionLabel", () => {
  it("affiche le libellé de la mission", () => {
    renderLabel();

    expect(screen.getByText("Portail bailleurs")).toBeInTheDocument();
  });

  it("n'affiche aucune infobulle tant que la souris est ailleurs", () => {
    renderLabel();

    expect(screen.queryByRole("tooltip")).toBeNull();
  });

  it("place le consommé et l'estimé dans l'infobulle", () => {
    survoler(renderLabel());

    expect(screen.getByRole("tooltip")).toHaveTextContent("3/20 jrs. estimés");
  });

  it("redonne le nom complet dans l'infobulle, car il peut être tronqué", () => {
    const name = "Automatisation du reporting de la direction financière";
    survoler(renderLabel({ label: name }));

    expect(screen.getByRole("tooltip")).toHaveTextContent(name);
  });

  it("suit le curseur", () => {
    const element = renderLabel();

    survoler(element, 100, 200);
    const premierePosition = screen.getByRole("tooltip").style.left;
    survoler(element, 300, 200);

    expect(screen.getByRole("tooltip").style.left).not.toBe(premierePosition);
  });

  it("se place à côté du curseur, sans le masquer", () => {
    survoler(renderLabel(), 100, 200);

    const tooltip = screen.getByRole("tooltip");
    expect(Number.parseInt(tooltip.style.left)).toBeGreaterThan(100);
    expect(Number.parseInt(tooltip.style.top)).toBeGreaterThan(200);
  });

  it("disparaît quand la souris quitte la cellule", () => {
    const element = renderLabel();
    survoler(element);

    fireEvent.mouseLeave(element);

    expect(screen.queryByRole("tooltip")).toBeNull();
  });

  it("n'affiche aucun ratio pour une activité sans estimé", () => {
    survoler(renderLabel({ label: "Absences", estimeJ: null }));

    expect(screen.getByRole("tooltip")).not.toHaveTextContent("estimés");
  });

  it("affiche un consommé nul comme zéro", () => {
    survoler(renderLabel({ label: "Support", consommeJ: 0, estimeJ: 5 }));

    expect(screen.getByRole("tooltip")).toHaveTextContent("0/5 jrs. estimés");
  });
});
