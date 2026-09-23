import { describe, expect, it, vi } from "vitest";
import { fireEvent, render, screen } from "@testing-library/react";

const push = vi.fn();
vi.mock("next/navigation", () => ({ useRouter: () => ({ push }) }));

import { NotificationItem } from "./NotificationItem";
import type { NotificationResponse } from "@/lib/api/generated/model";

const NOW = new Date("2026-09-17T12:00:00");

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

function renderItem(over: Partial<NotificationResponse> = {}, onToggle = vi.fn()) {
  render(
    <NotificationItem notification={line(over)} now={NOW} onToggleRead={onToggle} />,
  );
  return onToggle;
}

describe("NotificationItem", () => {
  it("reads as a sentence in French", () => {
    renderItem();

    expect(screen.getByText(/vous a ajouté comme référent sur/)).toBeInTheDocument();
    expect(screen.getByText("Nino Garo")).toBeInTheDocument();
    expect(screen.getByText("Refonte du site")).toBeInTheDocument();
  });

  it("says how long ago", () => {
    renderItem();

    expect(screen.getByText("il y a 2 h")).toBeInTheDocument();
  });

  it("leads to what it speaks of", () => {
    renderItem();

    expect(screen.getByRole("link")).toHaveAttribute("href", "/projects/42");
  });

  it("leads to the thread, on the update it speaks of", () => {
    renderItem({ kind: "project.update_posted", payload: { update_id: 412 } });

    expect(screen.getByRole("link")).toHaveAttribute(
      "href",
      "/notifications?mission=42&tab=updates&update=412",
    );
  });

  it("closes the lucarne it was read in", () => {
    const onFollow = vi.fn();
    render(
      <NotificationItem
        notification={line()}
        now={NOW}
        onToggleRead={vi.fn()}
        onFollow={onFollow}
      />,
    );

    fireEvent.click(screen.getByRole("link"));

    expect(onFollow).toHaveBeenCalled();
  });

  it("leads nowhere once the subject is gone", () => {
    renderItem({ kind: "project.deleted", project: null });

    expect(screen.queryByRole("link")).not.toBeInTheDocument();
  });

  it("offers to mark a waiting line as seen", () => {
    const onToggle = renderItem();

    fireEvent.click(screen.getByRole("button", { name: "Marquer comme lu" }));

    expect(onToggle).toHaveBeenCalledWith(1, true);
  });

  it("offers to put a seen line back in waiting", () => {
    const onToggle = renderItem({ read_at: "2026-09-17T11:00:00" });

    fireEvent.click(screen.getByRole("button", { name: "Marquer comme non lu" }));

    expect(onToggle).toHaveBeenCalledWith(1, false);
  });

  it("marks a waiting line so it is told apart at a glance", () => {
    renderItem();

    expect(screen.getByTestId("unread-mark")).toBeInTheDocument();
  });

  it("carries no mark once it has been seen", () => {
    renderItem({ read_at: "2026-09-17T11:00:00" });

    expect(screen.queryByTestId("unread-mark")).not.toBeInTheDocument();
  });

  it("says how many times the same gesture folded in", () => {
    renderItem({ kind: "timesheet.edited", day: "2026-01-01", count: 22 });

    expect(screen.getByText("22 modifications")).toBeInTheDocument();
  });
});
