import { describe, expect, it } from "vitest";
import { render } from "@testing-library/react";

import { Logo } from "./Logo";

describe("Logo", () => {
  it("stays out of the accessibility tree: the name is written beside it", () => {
    const { container } = render(<Logo />);

    expect(container.querySelector("svg")?.getAttribute("aria-hidden")).toBe("true");
  });

  it("takes its size and its colour from the caller", () => {
    const { container } = render(<Logo className="size-6 text-slate-500" />);
    const svg = container.querySelector("svg");

    expect(svg?.getAttribute("class")).toBe("size-6 text-slate-500");
    expect(svg?.getAttribute("fill")).toBe("currentColor");
  });

  it("leaves the outer ring of the grid empty, so the mark keeps its margin", () => {
    const { container } = render(<Logo />);

    const columns = [...container.querySelectorAll("rect")].map((cell) =>
      Number(cell.getAttribute("x")),
    );
    const rows = [...container.querySelectorAll("rect")].map((cell) =>
      Number(cell.getAttribute("y")),
    );

    const step = 64 / 7;
    expect(Math.min(...columns, ...rows)).toBeGreaterThan(step / 2);
    expect(Math.max(...columns, ...rows)).toBeLessThan(64 - step);
  });
});
