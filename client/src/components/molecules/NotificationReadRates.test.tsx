import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/react";

import { NotificationReadRates } from "./NotificationReadRates";

const READING = {
  delivered: 10,
  read: 6,
  read_rate: 0.6,
  unread: 3,
  ignored: 1,
  kinds: [
    { kind: "project.update_posted" as const, delivered: 6, read: 2, read_rate: 2 / 6 },
    { kind: "update.mention" as const, delivered: 4, read: 4, read_rate: 1 },
  ],
};

describe("NotificationReadRates", () => {
  it("lists the kinds in the order the server gave, least opened first", () => {
    render(<NotificationReadRates reading={READING} />);

    const rows = screen.getAllByRole("listitem").map((row) => row.textContent);
    expect(rows[0]).toContain("Actualités de projet");
    expect(rows[1]).toContain("Mentions");
  });

  it("says how many were opened out of how many were sent", () => {
    render(<NotificationReadRates reading={READING} />);

    expect(screen.getByText("2 / 6")).toBeInTheDocument();
    expect(screen.getByText("33 %")).toBeInTheDocument();
  });

  it("says so in words when nothing was sent", () => {
    render(<NotificationReadRates reading={{ ...READING, kinds: [] }} />);

    expect(
      screen.getByText("Aucune notification envoyée sur la période."),
    ).toBeInTheDocument();
  });
});
