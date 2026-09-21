import { describe, expect, it } from "vitest";

import {
  formatParisDateTime,
  formatParisMoment,
  formatParisTime,
  parisDay,
} from "@/lib/instants";

describe("instants read on the Paris clock", () => {
  it("shows the hour it was in Paris, not the one the server counted in", () => {
    expect(formatParisTime("2026-09-20T08:30:00+00:00")).toBe("10:30");
  });

  it("follows the winter offset without being told", () => {
    expect(formatParisTime("2026-01-20T08:30:00+00:00")).toBe("09:30");
  });

  it("names the day Paris is on, not the one UTC is still on", () => {
    expect(parisDay("2026-07-20T23:30:00+00:00")).toBe("2026-07-21");
  });

  it("keeps the day when the two clocks agree on it", () => {
    expect(parisDay("2026-07-20T09:00:00+00:00")).toBe("2026-07-20");
  });

  it("spells out an instant in full", () => {
    expect(formatParisDateTime("2026-07-20T23:30:00+00:00")).toBe("21/07/2026 à 01:30");
  });

  it("pads an hour before ten", () => {
    expect(formatParisTime("2026-01-20T07:05:00+00:00")).toBe("08:05");
  });

  it("reads midnight as 00, never as 24", () => {
    expect(formatParisTime("2026-01-19T23:00:00+00:00")).toBe("00:00");
  });
});

describe("formatParisMoment", () => {
  it("says the hour rather than showing it", () => {
    expect(formatParisMoment("2026-05-20T11:35:00+00:00")).toBe("20/05/2026 à 13h35");
  });

  it("keeps the leading zero of a minute", () => {
    expect(formatParisMoment("2026-05-20T11:05:00+00:00")).toBe("20/05/2026 à 13h05");
  });

  it("reads the Paris hour, not the reader's", () => {
    expect(formatParisMoment("2026-01-15T23:30:00+00:00")).toBe("16/01/2026 à 00h30");
  });
});
