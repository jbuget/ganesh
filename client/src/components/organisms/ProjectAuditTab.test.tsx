import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { ProjectAuditTab } from "./ProjectAuditTab";
import type { AuditLogEntryResponse } from "@/lib/api/generated/model";

const api = vi.hoisted(() => ({ listProjectAuditLog: vi.fn() }));

vi.mock("@/lib/api/generated/projects/projects", () => api);

const LIN = { id: 1, display_name: "Lin Chen", initials: "LC" };

function line(id: number, at: string): AuditLogEntryResponse {
  return {
    id,
    at,
    action: "project.create",
    actor: LIN,
    target_user: null,
    project: null,
    day: null,
    field: null,
    old_value: null,
    new_value: null,
  };
}

function served(total: number, entries: AuditLogEntryResponse[]) {
  api.listProjectAuditLog.mockResolvedValue({ data: { total, entries } });
}

beforeEach(() => {
  vi.clearAllMocks();
  served(0, []);
});

describe("ProjectAuditTab", () => {
  it("says so plainly when nothing has happened yet", async () => {
    render(<ProjectAuditTab projectId={7} />);

    expect(
      await screen.findByText("Rien n'a encore été enregistré sur ce projet."),
    ).toBeInTheDocument();
  });

  it("gathers the gestures under the day they were made", async () => {
    served(2, [line(1, "2026-09-17T12:05:00Z"), line(2, "2026-09-16T07:00:00Z")]);

    render(<ProjectAuditTab projectId={7} />);

    expect(await screen.findByText("17 sept. 2026")).toBeInTheDocument();
    expect(screen.getByText("16 sept. 2026")).toBeInTheDocument();
  });

  it("counts the whole log, not the page one is reading", async () => {
    served(340, [line(1, "2026-09-17T12:05:00Z")]);

    render(<ProjectAuditTab projectId={7} />);

    expect(await screen.findByText("340 gestes enregistrés")).toBeInTheDocument();
  });

  it("offers the rest of the log, and asks for the page after the one read", async () => {
    served(3, [line(1, "2026-09-17T12:05:00Z")]);

    render(<ProjectAuditTab projectId={7} />);
    await userEvent.click(await screen.findByRole("button", { name: "Voir plus" }));

    await waitFor(() =>
      expect(api.listProjectAuditLog).toHaveBeenLastCalledWith(7, {
        limit: 50,
        offset: 1,
      }),
    );
  });

  it("offers nothing more once the whole log is on screen", async () => {
    served(1, [line(1, "2026-09-17T12:05:00Z")]);

    render(<ProjectAuditTab projectId={7} />);

    expect(await screen.findByText("1 geste enregistré")).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "Voir plus" })).toBeNull();
  });
});
