import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { UserAuditTab } from "./UserAuditTab";
import type { AuditLogEntryResponse } from "@/lib/api/generated/model";

const api = vi.hoisted(() => ({ listUserAuditLog: vi.fn() }));

vi.mock("@/lib/api/generated/users/users", () => api);

const LIN = { id: 1, display_name: "Lin Chen", initials: "LC" };
const NINO = { id: 2, display_name: "Nino Garo", initials: "NG" };

function line(
  id: number,
  at: string,
  over: Partial<AuditLogEntryResponse> = {},
): AuditLogEntryResponse {
  return {
    id,
    at,
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

function served(total: number, entries: AuditLogEntryResponse[]) {
  api.listUserAuditLog.mockResolvedValue({ data: { total, entries } });
}

beforeEach(() => {
  vi.clearAllMocks();
  served(0, []);
});

describe("UserAuditTab", () => {
  it("says so plainly when nothing has happened yet", async () => {
    render(<UserAuditTab userId={1} />);

    expect(
      await screen.findByText("Rien n'a encore été enregistré sur cette personne."),
    ).toBeInTheDocument();
  });

  it("names the mission of every line: the panel is a person, not a project", async () => {
    served(1, [
      line(1, "2026-09-17T12:05:00Z", {
        project: { id: 4, label: "WAATcher" },
      }),
    ]);

    render(<UserAuditTab userId={1} />);

    expect(await screen.findByText("WAATcher")).toBeInTheDocument();
  });

  it("names whoever acted, half the lines having been written by somebody else", async () => {
    served(2, [
      line(1, "2026-09-17T12:05:00Z", {
        action: "user.role_change",
        actor: NINO,
        target_user: LIN,
        old_value: "TEAMMATE",
        new_value: "MANAGER",
      }),
      line(2, "2026-09-17T09:00:00Z"),
    ]);

    render(<UserAuditTab userId={1} />);

    expect(await screen.findByText("Nino Garo")).toBeInTheDocument();
    expect(screen.getByText("Lin Chen")).toBeInTheDocument();
    expect(screen.getByText(/a changé le rôle de Lin Chen/)).toBeInTheDocument();
  });

  it("counts the whole log, not the page one is reading", async () => {
    served(340, [line(1, "2026-09-17T12:05:00Z")]);

    render(<UserAuditTab userId={1} />);

    expect(await screen.findByText("340 gestes enregistrés")).toBeInTheDocument();
  });

  it("offers the rest of the log, and asks for the page after the one read", async () => {
    served(3, [line(1, "2026-09-17T12:05:00Z")]);

    render(<UserAuditTab userId={1} />);
    await userEvent.click(await screen.findByRole("button", { name: "Voir plus" }));

    await waitFor(() =>
      expect(api.listUserAuditLog).toHaveBeenLastCalledWith(1, {
        limit: 50,
        offset: 1,
      }),
    );
  });

  it("offers nothing more once the whole log is on screen", async () => {
    served(1, [line(1, "2026-09-17T12:05:00Z")]);

    render(<UserAuditTab userId={1} />);

    expect(await screen.findByText("1 geste enregistré")).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "Voir plus" })).toBeNull();
  });
});
