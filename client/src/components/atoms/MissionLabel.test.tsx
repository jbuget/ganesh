import { describe, expect, it } from "vitest";
import { fireEvent, render, screen } from "@testing-library/react";

import { MissionLabel } from "./MissionLabel";

function renderLabel(props: Partial<React.ComponentProps<typeof MissionLabel>> = {}) {
  render(
    <MissionLabel
      label="Portail bailleurs"
      consumedDays={3}
      estimatedDays={20}
      {...props}
    />,
  );
  return screen.getByText(props.label ?? "Portail bailleurs").parentElement!;
}

function hover(element: HTMLElement, x = 100, y = 200) {
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
    hover(renderLabel());

    expect(screen.getByRole("tooltip")).toHaveTextContent("3/20 jrs. estimés");
  });

  it("gives the full name back in the tooltip, since it may be truncated", () => {
    const name = "Automatisation du reporting de la direction financière";
    hover(renderLabel({ label: name }));

    expect(screen.getByRole("tooltip")).toHaveTextContent(name);
  });

  it("follows the cursor", () => {
    const element = renderLabel();

    hover(element, 100, 200);
    const firstPosition = screen.getByRole("tooltip").style.left;
    hover(element, 300, 200);

    expect(screen.getByRole("tooltip").style.left).not.toBe(firstPosition);
  });

  it("sits beside the cursor, without hiding it", () => {
    hover(renderLabel(), 100, 200);

    const tooltip = screen.getByRole("tooltip");
    expect(Number.parseInt(tooltip.style.left)).toBeGreaterThan(100);
    expect(Number.parseInt(tooltip.style.top)).toBeGreaterThan(200);
  });

  it("disappears when the mouse leaves the cell", () => {
    const element = renderLabel();
    hover(element);

    fireEvent.mouseLeave(element);

    expect(screen.queryByRole("tooltip")).toBeNull();
  });

  it("shows no ratio for work with no estimate", () => {
    hover(renderLabel({ label: "Absences", estimatedDays: null }));

    expect(screen.getByRole("tooltip")).not.toHaveTextContent("estimés");
  });

  it("shows a null consumption as zero", () => {
    hover(renderLabel({ label: "Support", consumedDays: 0, estimatedDays: 5 }));

    expect(screen.getByRole("tooltip")).toHaveTextContent("0/5 jrs. estimés");
  });
});

describe("MissionLabel, with a fractional estimate", () => {
  /**
   * Estimates are declared in days and some of them carry a half — « 23,5 ».
   * Shown raw it came out « 23.5 », with an English point, right beside a
   * consumed figure written « 8,75 » with a French comma.
   */
  it("writes the estimate the French way, as it writes the days consumed", () => {
    hover(renderLabel({ label: "DOE", consumedDays: 8.75, estimatedDays: 23.5 }));

    const tooltip = screen.getByRole("tooltip");
    expect(tooltip).toHaveTextContent("8,75/23,5 jrs. estimés");
    expect(tooltip.textContent).not.toContain("23.5");
  });
});
