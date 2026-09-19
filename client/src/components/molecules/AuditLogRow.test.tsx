import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { AuditLogRow } from "./AuditLogRow";
import type { AuditLogEntryResponse } from "@/lib/api/generated/model";

const LIN = { id: 1, display_name: "Lin Chen", initials: "LC" };

function entry(over: Partial<AuditLogEntryResponse> = {}): AuditLogEntryResponse {
  return {
    id: 1,
    at: "2026-09-17T14:05:00",
    action: "project.create",
    actor: LIN,
    target_user: null,
    day: null,
    field: null,
    old_value: null,
    new_value: null,
    ...over,
  };
}

function row(over: Partial<AuditLogEntryResponse> = {}) {
  render(
    <ul>
      <AuditLogRow entry={entry(over)} />
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
});
