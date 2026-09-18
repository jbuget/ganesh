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
  it("shows the mission label", () => {
    renderLabel();

    expect(screen.getByText("Portail bailleurs")).toBeInTheDocument();
  });

  it("shows no tooltip while the mouse is elsewhere", () => {
    renderLabel();

    expect(screen.queryByRole("tooltip")).toBeNull();
  });

  it("puts consumed and estimated in the tooltip", () => {
    survoler(renderLabel());

    expect(screen.getByRole("tooltip")).toHaveTextContent("3/20 jrs. estimés");
  });

  it("gives the full name back in the tooltip, since it may be truncated", () => {
    const name = "Automatisation du reporting de la direction financière";
    survoler(renderLabel({ label: name }));

    expect(screen.getByRole("tooltip")).toHaveTextContent(name);
  });

  it("follows the cursor", () => {
    const element = renderLabel();

    survoler(element, 100, 200);
    const firstPosition = screen.getByRole("tooltip").style.left;
    survoler(element, 300, 200);

    expect(screen.getByRole("tooltip").style.left).not.toBe(firstPosition);
  });

  it("sits beside the cursor, without hiding it", () => {
    survoler(renderLabel(), 100, 200);

    const tooltip = screen.getByRole("tooltip");
    expect(Number.parseInt(tooltip.style.left)).toBeGreaterThan(100);
    expect(Number.parseInt(tooltip.style.top)).toBeGreaterThan(200);
  });

  it("disappears when the mouse leaves the cell", () => {
    const element = renderLabel();
    survoler(element);

    fireEvent.mouseLeave(element);

    expect(screen.queryByRole("tooltip")).toBeNull();
  });

  it("shows no ratio for work with no estimate", () => {
    survoler(renderLabel({ label: "Absences", estimeJ: null }));

    expect(screen.getByRole("tooltip")).not.toHaveTextContent("estimés");
  });

  it("shows a null consumption as zero", () => {
    survoler(renderLabel({ label: "Support", consommeJ: 0, estimeJ: 5 }));

    expect(screen.getByRole("tooltip")).toHaveTextContent("0/5 jrs. estimés");
  });
});
