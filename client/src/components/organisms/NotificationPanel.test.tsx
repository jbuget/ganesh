import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { NotificationPanel } from "./NotificationPanel";
import type { NotificationResponse } from "@/lib/api/generated/model";

const inbox = vi.hoisted(() => ({ state: {} as Record<string, unknown> }));

vi.mock("@/lib/use-inbox", () => ({ useInbox: () => inbox.state }));

vi.mock("next/navigation", () => ({ useRouter: () => ({ push: vi.fn() }) }));

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
  inbox.state = {
    entries: [],
    total: 0,
    unreadCount: 0,
    isLoading: false,
    isSettling: false,
    toggleRead: vi.fn(),
    markAllRead: vi.fn(),
    ...overrides,
  };
  render(<NotificationPanel />);
}

describe("NotificationPanel", () => {
  it("rings with what is waiting", () => {
    show({ unreadCount: 4 });

    expect(screen.getByRole("button")).toHaveAccessibleName(
      "Notifications, 4 non lues",
    );
  });

  it("holds the list closed until it is opened", () => {
    show({ entries: [line()], unreadCount: 1 });

    expect(screen.queryByText("Refonte du site")).not.toBeInTheDocument();
  });
});
