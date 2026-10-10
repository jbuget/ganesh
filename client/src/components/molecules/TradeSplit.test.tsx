import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/react";

import { TradeSplit } from "./TradeSplit";

const STEERING = {
  project_days: 9,
  off_project_days: 1,
  project_share: 0.9,
  by_status: [],
  by_category: [],
  top_missions: [],
  by_nature: [
    { nature: "development" as const, days: 6, share: 0.6 },
    { nature: null, days: 3, share: 0.3 },
  ],
};

describe("TradeSplit", () => {
  it("names the trades, and the days that state none", () => {
    render(<TradeSplit steering={STEERING} />);

    expect(screen.getByText("Développement")).toBeInTheDocument();
    expect(screen.getByText("Sans métier précisé")).toBeInTheDocument();
  });

  it("says so in words when nothing was declared", () => {
    render(<TradeSplit steering={{ ...STEERING, project_days: 0, by_nature: [] }} />);

    expect(screen.getByText("Aucune saisie sur la période.")).toBeInTheDocument();
  });
});
