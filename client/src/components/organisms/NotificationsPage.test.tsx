import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { NotificationsPage } from "./NotificationsPage";
import type { NotificationResponse } from "@/lib/api/generated/model";

const inbox = vi.hoisted(() => ({ state: {} as Record<string, unknown> }));

vi.mock("@/lib/use-inbox", () => ({ useInbox: () => inbox.state, PAGE_SIZE: 20 }));

function line(over: Partial<NotificationResponse> = {}): NotificationResponse {
  return {
    id: 1,
    at: "2026-09-17T10:00:00",
    kind: "project.assigned",
    actor: { id: 2, display_name: "Nino Garo", initials: "NG" },
    project: { id: 42, label: "Refonte du site" },
    day: null,
    count: 1,
    read_at: null,
    payload: { role: "referent" },
    ...over,
  };
}

function show(overrides: Record<string, unknown> = {}) {
  const state = {
    entries: [],
    total: 0,
    unreadCount: 0,
    filter: "all",
    page: 0,
    pageSize: 20,
    hasMore: false,
    isLoading: false,
    isSettling: false,
    show: vi.fn(),
    goToPage: vi.fn(),
    toggleRead: vi.fn(),
    markAllRead: vi.fn(),
    ...overrides,
  };
  inbox.state = state;
  render(<NotificationsPage />);
  return state;
}

describe("NotificationsPage", () => {
  it("says so when there is nothing to read", () => {
    show();

    expect(screen.getByText("Aucune notification.")).toBeInTheDocument();
  });

  it("lists what one has been told", () => {
    show({ entries: [line()], total: 1, unreadCount: 1 });

    expect(screen.getByText("Refonte du site")).toBeInTheDocument();
  });

  it("offers to read only what is waiting", () => {
    const state = show({ entries: [line()], total: 1, unreadCount: 1 });

    fireEvent.click(screen.getByRole("button", { name: /Non lues/ }));

    expect(state.show).toHaveBeenCalledWith("unread");
  });

  it("counts what is waiting on the filter itself", () => {
    show({ entries: [line()], total: 1, unreadCount: 3 });

    expect(screen.getByRole("button", { name: "Non lues (3)" })).toBeInTheDocument();
  });

  it("marks everything seen at once", () => {
    const state = show({ entries: [line()], total: 1, unreadCount: 1 });

    fireEvent.click(screen.getByRole("button", { name: "Tout marquer comme lu" }));

    expect(state.markAllRead).toHaveBeenCalled();
  });

  it("offers nothing to mark when nothing is waiting", () => {
    show({ entries: [line({ read_at: "2026-09-17T11:00:00" })], total: 1 });

    expect(
      screen.queryByRole("button", { name: "Tout marquer comme lu" }),
    ).not.toBeInTheDocument();
  });

  it("says where one is in the list", () => {
    show({ entries: [line()], total: 42, unreadCount: 1, hasMore: true });

    expect(screen.getByText("1–20 sur 42")).toBeInTheDocument();
  });

  it("goes on to the next page", () => {
    const state = show({ entries: [line()], total: 42, hasMore: true });

    fireEvent.click(screen.getByRole("button", { name: "Page suivante" }));

    expect(state.goToPage).toHaveBeenCalledWith(1);
  });

  it("holds back the first page", () => {
    show({ entries: [line()], total: 42, hasMore: true });

    expect(screen.getByRole("button", { name: "Page précédente" })).toBeDisabled();
  });

  it("shows no paging on a list that fits", () => {
    show({ entries: [line()], total: 1 });

    expect(
      screen.queryByRole("button", { name: "Page suivante" }),
    ).not.toBeInTheDocument();
  });
});
