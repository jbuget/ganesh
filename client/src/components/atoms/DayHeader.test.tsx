import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/react";

import { DayHeader } from "./DayHeader";

const baseProps = {
  day: "2026-09-15",
  isOffDay: false,
  isToday: false,
  label: null,
};

/**
 * A header cell lives in a table row. Rendering it outside that context would
 * hide an invalid HTML structure, which silently breaks React hydration.
 */
function renderInRow(ui: React.ReactElement) {
  return render(
    <table>
      <thead>
        <tr>{ui}</tr>
      </thead>
    </table>,
  );
}

describe("DayHeader", () => {
  it("marks today", () => {
    renderInRow(<DayHeader {...baseProps} isToday />);

    expect(screen.getByRole("columnheader").className).toContain("bg-amber-100");
  });

  it("greys a non-working day", () => {
    renderInRow(<DayHeader {...baseProps} isOffDay />);

    expect(screen.getByRole("columnheader").className).toContain("bg-slate-100");
  });

  it("marks today even when it is a non-working day", () => {
    // Where one is in the month is read off this band, and a Saturday is a day
    // like any other for that: greying today away would take the landmark out
    // of the header on two days out of seven.
    renderInRow(<DayHeader {...baseProps} isOffDay isToday />);

    expect(screen.getByRole("columnheader").className).toContain("bg-amber-100");
  });
});
