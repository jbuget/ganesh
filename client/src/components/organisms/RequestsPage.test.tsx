import { beforeEach, describe, expect, it, vi } from "vitest";
import { render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import type { RequestResponse, UserResponse } from "@/lib/api/generated/model";
import { EVERY_REQUEST } from "@/lib/request-filters";

import { RequestsPage } from "./RequestsPage";

const MANAGER: UserResponse = {
  id: 1,
  email: "j.buget@waat.fr",
  display_name: "J. Buget",
  initials: "JB",
  role: "MANAGER",
  is_active: true,
};

const HANDED: RequestResponse = {
  id: 5,
  title: "Relances de paiement à la main",
  state: "submitted",
  requester: { id: 7, label: "Anne Métier" },
  sponsors: [{ id: 3, label: "C. Direction" }],
  departments: ["finance_admin"],
  created_at: "2026-09-22T10:00:00Z",
  submitted_at: "2026-09-23T08:00:00Z",
  problem: "Tapées une par une.",
  impact: "Trois personnes.",
  expected_outcome: "Une relance automatique.",
};

const state = vi.hoisted(() => ({
  requests: [] as RequestResponse[],
  user: undefined as UserResponse | undefined,
  decide: vi.fn(),
  opened: null as number | null,
}));

vi.mock("@/lib/use-requests", () => ({
  useRequestsScreen: () => ({
    requests: state.requests,
    isLoading: false,
    user: state.user,
    visible: state.requests.length,
    total: state.requests.length,
    find: (id: number) => state.requests.find((r) => r.id === id) ?? null,
    file: vi.fn(),
    fillIn: vi.fn(),
    submit: vi.fn(),
    withdraw: vi.fn(),
    remove: vi.fn(),
    decide: state.decide,
  }),
}));

vi.mock("@/lib/use-request-filters", () => ({
  useRequestFilters: () => ({
    filters: EVERY_REQUEST,
    hasFilter: false,
    set: vi.fn(),
    clear: vi.fn(),
  }),
}));

vi.mock("@/lib/opened-request", () => ({
  useOpenedRequest: () => ({
    openedRequest: state.opened,
    open: vi.fn(),
    close: vi.fn(),
  }),
}));

vi.mock("@/lib/api/queries", () => ({
  useRequestSponsors: () => ({ sponsors: [{ id: 3, label: "C. Direction" }] }),
}));

describe("RequestsPage", () => {
  beforeEach(() => {
    state.requests = [HANDED];
    state.user = MANAGER;
    state.opened = null;
    state.decide.mockClear();
  });

  it("names the need, who asked for it and who carries it", () => {
    render(<RequestsPage />);

    const row = screen.getByRole("row", { name: /Relances/ });
    expect(within(row).getByText("Anne Métier")).toBeInTheDocument();
    expect(within(row).getByText("C. Direction")).toBeInTheDocument();
    expect(within(row).getByText("Soumise")).toBeInTheDocument();
  });

  it("offers a manager the three things arbitrating can say", () => {
    state.opened = HANDED.id;

    render(<RequestsPage />);

    const panel = within(screen.getByRole("complementary"));
    expect(panel.getByRole("button", { name: "Accepter" })).toBeInTheDocument();
    expect(panel.getByRole("button", { name: "Plus tard" })).toBeInTheDocument();
    expect(panel.getByRole("button", { name: "Refuser" })).toBeInTheDocument();
  });

  it("offers nothing to a teammate", () => {
    state.opened = HANDED.id;
    state.user = { ...MANAGER, role: "TEAMMATE" };

    render(<RequestsPage />);

    expect(screen.queryByRole("button", { name: "Accepter" })).toBeNull();
  });

  it("offers nothing to the manager who carries the need", () => {
    state.opened = HANDED.id;
    state.requests = [{ ...HANDED, sponsors: [{ id: 1, label: "J. Buget" }] }];

    render(<RequestsPage />);

    expect(screen.queryByRole("button", { name: "Accepter" })).toBeNull();
  });

  it("refuses to turn a need down without a reason", async () => {
    state.opened = HANDED.id;

    render(<RequestsPage />);
    await userEvent.click(
      within(screen.getByRole("complementary")).getByRole("button", {
        name: "Refuser",
      }),
    );

    const dialog = within(screen.getByRole("dialog"));
    expect(dialog.getByRole("button", { name: "Confirmer" })).toBeDisabled();
  });

  it("records the decision and what was said of it", async () => {
    state.opened = HANDED.id;

    render(<RequestsPage />);
    await userEvent.click(
      within(screen.getByRole("complementary")).getByRole("button", {
        name: "Refuser",
      }),
    );
    const dialog = within(screen.getByRole("dialog"));
    await userEvent.type(dialog.getByRole("textbox"), "Déjà couvert.");
    await userEvent.click(dialog.getByRole("button", { name: "Confirmer" }));

    expect(state.decide).toHaveBeenCalledWith(5, "rejected", "Déjà couvert.");
  });
});
