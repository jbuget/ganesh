import { fireEvent, render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { NotificationsPage } from "./NotificationsPage";
import type { NotificationResponse } from "@/lib/api/generated/model";

const inbox = vi.hoisted(() => ({ state: {} as Record<string, unknown> }));
const signedIn = vi.hoisted(() => ({ role: "TEAMMATE" as string }));

vi.mock("@/lib/use-inbox", () => ({ useInbox: () => inbox.state, PAGE_SIZE: 20 }));

/** Only the role is read here: it decides whether the manager panel shows. */
vi.mock("@/lib/api/queries", async (importOriginal) => ({
  ...(await importOriginal<Record<string, unknown>>()),
  useCurrentUser: () => ({ user: { id: 1, role: signedIn.role } }),
}));

vi.mock("@/lib/use-reminders", () => ({
  useReminderRuns: () => ({ isRunning: false, outcome: null, run: vi.fn() }),
}));

vi.mock("next/navigation", () => ({ useRouter: () => ({ push: vi.fn() }) }));

/**
 * The panel reads the mission from the server and has its own tests: what is
 * asked here is only whether the inbox opens it, on which mission, and on
 * which line of its thread.
 */
vi.mock("@/components/organisms/ProjectPanel", () => ({
  ProjectPanel: ({
    projectId,
    tab,
    aimedAt,
  }: {
    projectId: number;
    tab?: string | null;
    aimedAt?: number | null;
  }) => <aside aria-label={`Projet ${projectId} · ${tab} · ${aimedAt}`} />,
}));

beforeEach(() => {
  // The open panel lives in the address, and a line only opens one on the
  // screen it points at: the inbox is where these tests stand.
  window.history.replaceState(null, "", "/notifications");
  signedIn.role = "TEAMMATE";
});

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
    payload: { role: "lead" },
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
  it("opens the project beside the list, on the update one was told about", () => {
    show({
      entries: [line({ kind: "project.update_posted", payload: { update_id: 412 } })],
      total: 1,
      unreadCount: 1,
    });

    fireEvent.click(screen.getByRole("link"));

    expect(
      screen.getByRole("complementary", { name: "Projet 42 · updates · 412" }),
    ).toBeInTheDocument();
  });

  it("holds no panel until a line is followed", () => {
    show({ entries: [line()], total: 1, unreadCount: 1 });

    expect(screen.queryByRole("complementary")).not.toBeInTheDocument();
  });

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

describe("the round a manager sends by hand", () => {
  it("is offered to a manager, at the foot of their own inbox", () => {
    signedIn.role = "MANAGER";
    render(<NotificationsPage />);

    expect(screen.getByText("Rappels par e-mail")).toBeInTheDocument();
  });

  it("is not offered to a teammate", () => {
    // It writes to the whole team at once.
    signedIn.role = "TEAMMATE";
    render(<NotificationsPage />);

    expect(screen.queryByText("Rappels par e-mail")).not.toBeInTheDocument();
  });
});
