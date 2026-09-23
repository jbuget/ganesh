import { describe, expect, it, vi } from "vitest";
import { render, screen } from "@testing-library/react";

import { AuditLogPage } from "./AuditLogPage";
import { NO_FILTER, type AuditFilters } from "@/lib/audit-filters";

const state = vi.hoisted(() => ({
  log: {
    entries: [] as unknown[],
    total: 0,
    busy: false,
    hasMore: false,
    loadMore: vi.fn(),
  },
  filters: { actions: [], actorIds: [], fromDay: "", toDay: "" } as AuditFilters,
  change: vi.fn(),
  clear: vi.fn(),
}));

vi.mock("@/lib/use-audit-log", () => ({ useAuditLog: () => state }));

vi.mock("@/lib/api/queries", () => ({
  useTeammates: () => ({ teammates: [] }),
}));

describe("AuditLogPage", () => {
  it("names itself as the register read across", () => {
    render(<AuditLogPage />);

    expect(screen.getByText("Journal")).toBeInTheDocument();
  });

  /**
   * An empty register and a filter that matches nothing are not the same
   * fact. Saying « rien n'a été enregistré » on a filtered screen would have
   * the reader believe the register is empty.
   */
  it("tells an empty register from criteria nothing answers", () => {
    state.filters = NO_FILTER;
    const { unmount } = render(<AuditLogPage />);
    expect(screen.getByText("Rien n'a encore été enregistré.")).toBeInTheDocument();
    unmount();

    state.filters = { ...NO_FILTER, actions: ["project.delete"] };
    render(<AuditLogPage />);
    expect(
      screen.getByText("Aucun geste ne répond à ces critères."),
    ).toBeInTheDocument();
  });
});
