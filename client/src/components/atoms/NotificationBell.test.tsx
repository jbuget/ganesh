import { describe, expect, it, vi } from "vitest";
import { fireEvent, render, screen } from "@testing-library/react";

import { NotificationBell } from "./NotificationBell";

describe("NotificationBell", () => {
  it("says how many are waiting", () => {
    render(<NotificationBell unreadCount={3} />);

    expect(screen.getByRole("button")).toHaveAccessibleName(
      "Notifications, 3 non lues",
    );
  });

  it("says it in the singular for one", () => {
    render(<NotificationBell unreadCount={1} />);

    expect(screen.getByRole("button")).toHaveAccessibleName("Notifications, 1 non lue");
  });

  it("carries no mark when nothing is waiting", () => {
    render(<NotificationBell unreadCount={0} />);

    expect(screen.getByRole("button")).toHaveAccessibleName("Notifications");
    expect(screen.queryByText("0")).not.toBeInTheDocument();
  });

  it("shows the count unfolded", () => {
    render(<NotificationBell unreadCount={7} />);

    expect(screen.getByText("7")).toBeInTheDocument();
  });

  it("stops counting past what a badge can hold", () => {
    render(<NotificationBell unreadCount={120} />);

    expect(screen.getByText("99+")).toBeInTheDocument();
    // The exact figure is still said out loud, where there is room for it.
    expect(screen.getByRole("button")).toHaveAccessibleName(
      "Notifications, 120 non lues",
    );
  });

  it("gives its width back once folded: the icon and a bare dot", () => {
    render(<NotificationBell unreadCount={7} collapsed />);

    expect(screen.queryByText("7")).not.toBeInTheDocument();
    expect(screen.queryByText("Notifications")).not.toBeInTheDocument();
    expect(screen.getByRole("button")).toHaveAccessibleName(
      "Notifications, 7 non lues",
    );
  });

  it("hands its click on to whoever opens the panel", () => {
    const onClick = vi.fn();
    render(<NotificationBell unreadCount={0} onClick={onClick} />);

    fireEvent.click(screen.getByRole("button"));

    expect(onClick).toHaveBeenCalled();
  });
});
