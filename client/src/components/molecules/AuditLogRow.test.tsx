import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { AuditLogRow } from "./AuditLogRow";
import type { AuditLogEntryResponse } from "@/lib/api/generated/model";
import type { AuditReading } from "@/lib/audit-log";

const LIN = { id: 1, display_name: "Lin Chen", initials: "LC" };

function entry(over: Partial<AuditLogEntryResponse> = {}): AuditLogEntryResponse {
  return {
    id: 1,
    at: "2026-09-17T12:05:00Z",
    action: "project.create",
    actor: LIN,
    target_user: null,
    project: null,
    day: null,
    field: null,
    note: null,
    old_value: null,
    new_value: null,
    ...over,
  };
}

function row(over: Partial<AuditLogEntryResponse> = {}, reading?: AuditReading) {
  render(
    <ul>
      <AuditLogRow entry={entry(over)} reading={reading} />
    </ul>,
  );
}

describe("AuditLogRow", () => {
  it("says who did what, and at what time", () => {
    row();

    expect(screen.getByText("Lin Chen")).toBeInTheDocument();
    expect(screen.getByText("a créé le projet")).toBeInTheDocument();
    expect(screen.getByText("14:05")).toBeInTheDocument();
  });

  it("tells the hour on the Paris clock, not the one the API counted in", () => {
    // The API records the instant in UTC; production counts in UTC too, and
    // showing that hour straight is what made a gesture read two hours early.
    row({ at: "2026-09-17T21:40:00Z" });

    expect(screen.getByText("23:40")).toBeInTheDocument();
  });

  it("shows both ends of a change", () => {
    row({
      action: "project.status_change",
      old_value: "scoping",
      new_value: "development",
    });

    expect(screen.getByText("a changé la phase")).toBeInTheDocument();
    expect(screen.getByText("Cadrage")).toBeInTheDocument();
    expect(screen.getByText("Réalisation")).toBeInTheDocument();
  });

  it("keeps a gesture whose author is gone, and says the account went", () => {
    row({ actor: null });

    expect(screen.getByText("Compte supprimé")).toBeInTheDocument();
    expect(screen.getByText("a créé le projet")).toBeInTheDocument();
  });

  it("names the mission a line is about, where the line carries one", () => {
    // Read out of its grid, a declaration no longer says what it was booked
    // on: the month's log is where that has to be said.
    row(
      {
        action: "entry.set",
        project: { id: 10, label: "WAATcher" },
        day: "2026-09-14",
        new_value: "1.0",
      },
      { read: "month" },
    );

    expect(screen.getByText("WAATcher")).toBeInTheDocument();
  });

  it("says nothing of a mission where the line carries none", () => {
    row({ action: "month.validate", day: "2026-09-01" }, { read: "month" });

    expect(screen.getByText("a validé le mois")).toBeInTheDocument();
  });
});
