import { describe, expect, it } from "vitest";

import type { MonthFillingResponse } from "@/lib/api/generated/model";
import { readMonths, windowLabel } from "@/lib/user-record";

const TODAY = "2026-09-17";

function filling(overrides: Partial<MonthFillingResponse> = {}): MonthFillingResponse {
  return {
    month: "2026-09-01",
    delivered: 0,
    forecast: 0,
    working_days: 22,
    elapsed_working_days: 13,
    state: "open",
    validated_at: null,
    ...overrides,
  };
}

describe("windowLabel", () => {
  it("says the stretch the declared time was read over", () => {
    expect(windowLabel("2026-08-19", "2026-09-17")).toBe("du 19 août au 17 sept.");
  });
});

describe("readMonths", () => {
  it("names the month in French", () => {
    const [september] = readMonths([filling()], TODAY);

    expect(september.label).toBe("septembre 2026");
  });

  it("tells the month running from the ones already over", () => {
    const [september, august] = readMonths(
      [filling(), filling({ month: "2026-08-01" })],
      TODAY,
    );

    expect(september.isRunning).toBe(true);
    expect(august.isRunning).toBe(false);
  });

  it("measures what is missing against the days already gone", () => {
    const [september] = readMonths([filling({ delivered: 10 })], TODAY);

    expect(september.missing).toBe(3);
  });

  it("reports nothing missing when the month is up to date", () => {
    const [september] = readMonths([filling({ delivered: 13 })], TODAY);

    expect(september.missing).toBe(0);
  });

  it("never reports a negative gap on a day declared twice over", () => {
    const [september] = readMonths([filling({ delivered: 15 })], TODAY);

    expect(september.missing).toBe(0);
  });

  it("draws the bar against the whole month, forecast set back from delivered", () => {
    const [september] = readMonths(
      [filling({ delivered: 11, forecast: 5.5, working_days: 22 })],
      TODAY,
    );

    expect(september.deliveredShare).toBe(50);
    expect(september.forecastShare).toBe(25);
  });

  it("keeps the bar inside its own width when more is declared than the month holds", () => {
    const [september] = readMonths(
      [filling({ delivered: 20, forecast: 10, working_days: 22 })],
      TODAY,
    );

    expect(september.deliveredShare + september.forecastShare).toBeLessThanOrEqual(100);
  });

  it("draws nothing on a month with no working day at all", () => {
    const [empty] = readMonths(
      [filling({ working_days: 0, elapsed_working_days: 0 })],
      TODAY,
    );

    expect(empty.deliveredShare).toBe(0);
    expect(empty.forecastShare).toBe(0);
    expect(empty.missing).toBe(0);
  });

  it("says a month is closed, and when", () => {
    const [august] = readMonths(
      [
        filling({
          month: "2026-08-01",
          state: "validated",
          validated_at: "2026-09-01T09:30:00",
        }),
      ],
      TODAY,
    );

    expect(august.isValidated).toBe(true);
    expect(august.validatedAt).toBe("2026-09-01T09:30:00");
  });
});
