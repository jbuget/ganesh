import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/react";

import { UserMonths } from "./UserMonths";
import type { MonthFillingResponse } from "@/lib/api/generated/model";

const TODAY = "2026-09-17";

const filling = (
  overrides: Partial<MonthFillingResponse> = {},
): MonthFillingResponse => ({
  month: "2026-09-01",
  delivered: 0,
  forecast: 0,
  working_days: 22,
  elapsed_working_days: 13,
  state: "open",
  validated_at: null,
  ...overrides,
});

function show(months: MonthFillingResponse[]) {
  return render(<UserMonths months={months} userId={7} today={TODAY} />);
}

describe("UserMonths", () => {
  it("names the month and what it holds against what it calls for", () => {
    show([filling({ delivered: 11 })]);

    expect(screen.getByText("septembre 2026")).toBeInTheDocument();
    expect(screen.getByText("11 j")).toBeInTheDocument();
    expect(screen.getByText("/ 22 j")).toBeInTheDocument();
  });

  it("counts what is owed against the days already gone", () => {
    show([filling({ delivered: 10 })]);

    expect(screen.getByText(/3 j à déclarer/)).toBeInTheDocument();
  });

  it("says nothing is owed on a month kept up to date", () => {
    show([filling({ delivered: 13 })]);

    expect(screen.getByText("à jour")).toBeInTheDocument();
  });

  it("tells what is only planned from what was delivered", () => {
    show([filling({ delivered: 13, forecast: 2 })]);

    expect(screen.getByText(/2 j prévus/)).toBeInTheDocument();
  });

  it("calls for a validation on a month over and complete", () => {
    show([
      filling({
        month: "2026-08-01",
        delivered: 21,
        working_days: 21,
        elapsed_working_days: 21,
      }),
    ]);

    expect(screen.getByText("à valider")).toBeInTheDocument();
  });

  it("says a month is closed", () => {
    show([
      filling({
        month: "2026-08-01",
        delivered: 21,
        working_days: 21,
        elapsed_working_days: 21,
        state: "validated",
        validated_at: "2026-09-01T09:30:00",
      }),
    ]);

    expect(screen.getByText("Validé")).toBeInTheDocument();
    expect(screen.queryByText("à valider")).not.toBeInTheDocument();
  });

  it("opens that month for that teammate", () => {
    show([filling()]);

    expect(screen.getByRole("link", { name: /septembre 2026/ })).toHaveAttribute(
      "href",
      "/timesheet?month=2026-09&user=7",
    );
  });
});
