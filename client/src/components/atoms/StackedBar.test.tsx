import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/react";

import { StackedBar } from "./StackedBar";

const SEGMENTS = [
  {
    key: "development",
    label: "Développement",
    days: 6,
    share: 2 / 3,
    colour: "#2a78d6",
  },
  {
    key: "none",
    label: "Sans métier précisé",
    days: 3,
    share: 1 / 3,
    colour: "#94a3b8",
  },
];

describe("StackedBar", () => {
  it("names every part with its days and its share", () => {
    render(<StackedBar segments={SEGMENTS} label="Temps par métier" />);

    expect(screen.getByText("Développement")).toBeInTheDocument();
    expect(screen.getByText("6 j")).toBeInTheDocument();
    expect(screen.getByText("67 %")).toBeInTheDocument();
    expect(screen.getByText("33 %")).toBeInTheDocument();
  });

  it("names the bar itself", () => {
    render(<StackedBar segments={SEGMENTS} label="Temps par métier" />);

    expect(screen.getByRole("img", { name: "Temps par métier" })).toBeInTheDocument();
  });

  it("sizes each part by its share", () => {
    const { container } = render(<StackedBar segments={SEGMENTS} label="Temps" />);

    const [first] = container.querySelectorAll<HTMLElement>("[role=img] > div");
    expect(first.style.width).toMatch(/^66\.6/);
  });
});
