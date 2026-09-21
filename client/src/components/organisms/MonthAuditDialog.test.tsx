import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { MonthAuditDialog } from "./MonthAuditDialog";
import type { AuditLogEntryResponse } from "@/lib/api/generated/model";

const api = vi.hoisted(() => ({ listMonthAuditLog: vi.fn() }));

vi.mock("@/lib/api/generated/months/months", () => api);

const LIN = { id: 1, display_name: "Lin Chen", initials: "LC" };

function declared(id: number, at: string): AuditLogEntryResponse {
  return {
    id,
    at,
    action: "entry.set",
    actor: LIN,
    target_user: LIN,
    project: { id: 10, label: "WAATcher" },
    day: "2026-09-14",
    field: null,
    old_value: null,
    new_value: "1.0",
  };
}

function served(total: number, entries: AuditLogEntryResponse[]) {
  api.listMonthAuditLog.mockResolvedValue({ data: { total, entries } });
}

function open(over: { userId?: number | null; teammate?: string | null } = {}) {
  render(
    <MonthAuditDialog
      open
      onOpenChange={() => {}}
      month="2026-09-01"
      label="septembre 2026"
      userId={over.userId === undefined ? 1 : over.userId}
      teammate={over.teammate ?? null}
    />,
  );
}

beforeEach(() => {
  vi.clearAllMocks();
  served(0, []);
});

describe("MonthAuditDialog", () => {
  it("says which month it is the life of", async () => {
    open();

    expect(await screen.findByText("Historique de septembre 2026")).toBeInTheDocument();
  });

  it("says whose month is being read, when it is not one's own", async () => {
    open({ teammate: "Nino Garo" });

    expect(
      await screen.findByText(
        "Ce qui a été fait sur le mois de Nino Garo, du plus récent au plus ancien.",
      ),
    ).toBeInTheDocument();
  });

  it("says so plainly when nothing has happened yet", async () => {
    open();

    expect(
      await screen.findByText("Rien n'a encore été enregistré sur ce mois."),
    ).toBeInTheDocument();
  });

  it("names the mission each gesture was about", async () => {
    // The grid carries it in its rows; a log read out of the grid would lose
    // the one thing that says what the day was booked on.
    served(1, [declared(1, "2026-09-14T12:05:00Z")]);

    open();

    expect(await screen.findByText("WAATcher")).toBeInTheDocument();
    expect(screen.getByText("a déclaré 1 j le 14 sept. 2026")).toBeInTheDocument();
  });

  it("counts the whole log, not the page one is reading", async () => {
    served(340, [declared(1, "2026-09-14T12:05:00Z")]);

    open();

    expect(await screen.findByText("340 gestes enregistrés")).toBeInTheDocument();
  });

  it("offers the rest of the log, and asks for the page after the one read", async () => {
    served(3, [declared(1, "2026-09-14T12:05:00Z")]);

    open();
    await userEvent.click(await screen.findByRole("button", { name: "Voir plus" }));

    await waitFor(() =>
      expect(api.listMonthAuditLog).toHaveBeenLastCalledWith("2026-09-01", {
        user_id: 1,
        limit: 50,
        offset: 1,
      }),
    );
  });

  it("asks for nobody's month while it does not know whose", async () => {
    open({ userId: null });

    expect(
      await screen.findByText("Rien n'a encore été enregistré sur ce mois."),
    ).toBeInTheDocument();
    expect(api.listMonthAuditLog).not.toHaveBeenCalled();
  });
});
