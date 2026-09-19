import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/react";

import { LandingDate } from "./LandingDate";

describe("LandingDate", () => {
  it("spells the projected landing out", () => {
    render(<LandingDate endsOn="2026-09-24" slippageDays={null} />);

    expect(screen.getByText("24 sept. 2026")).toBeInTheDocument();
  });

  it("says how late a landing is against the date announced", () => {
    render(<LandingDate endsOn="2026-09-24" slippageDays={5} />);

    expect(screen.getByText("5 jours de retard")).toBeInTheDocument();
  });

  it("says nothing of a mission with no date announced", () => {
    render(<LandingDate endsOn="2026-09-24" slippageDays={null} />);

    expect(screen.queryByText(/retard|avance|temps/)).not.toBeInTheDocument();
  });

  it("marks a late landing apart from one on time", () => {
    const marks = [5, 0].map((days) => {
      const { container, unmount } = render(
        <LandingDate endsOn="2026-09-24" slippageDays={days} />,
      );
      const mark = container.querySelector("span[aria-hidden]")?.className ?? "";
      unmount();
      return mark;
    });

    expect(marks[0]).not.toBe(marks[1]);
  });

  it("shows a dash when nothing lands inside the horizon", () => {
    render(<LandingDate endsOn={null} slippageDays={null} />);

    expect(screen.getByText("—")).toBeInTheDocument();
  });
});
