import { beforeEach, describe, expect, it, vi } from "vitest";
import { render, screen } from "@testing-library/react";

import { AppFrame } from "./AppFrame";

const user = vi.hoisted(() => ({
  current: null as { id: number; role: string } | null,
  isLoading: false,
}));
const replace = vi.hoisted(() => vi.fn());
const pathname = vi.hoisted(() => ({ current: "/" }));

vi.mock("@/lib/api/queries", () => ({
  useCurrentUser: () => ({ user: user.current, isLoading: user.isLoading }),
}));

vi.mock("next/navigation", () => ({
  usePathname: () => pathname.current,
  useRouter: () => ({ replace }),
}));

vi.mock("@/components/organisms/AppSidebar", () => ({
  AppSidebar: () => <nav aria-label="Navigation" />,
}));

vi.mock("@/components/organisms/CommandPalette", () => ({
  CommandPalette: () => null,
}));

// Both reach for a server of their own; what the frame is tested on is which
// of them it hangs, not what they draw.
vi.mock("@/components/organisms/ReadOnlyBanner", () => ({
  ReadOnlyBanner: () => null,
}));

vi.mock("@/components/organisms/MoodReminder", () => ({
  MoodReminder: () => <p>Le rappel du moral</p>,
}));

function draw() {
  render(
    <AppFrame>
      <p>L&apos;écran</p>
    </AppFrame>,
  );
}

describe("AppFrame", () => {
  beforeEach(() => {
    replace.mockClear();
    user.isLoading = false;
    pathname.current = "/";
  });

  it("gives the team its sidebar", () => {
    user.current = { id: 1, role: "TEAMMATE" };

    draw();

    expect(screen.getByRole("navigation", { name: "Navigation" })).toBeInTheDocument();
    expect(screen.getByText("L'écran")).toBeInTheDocument();
  });

  it("opens no door to whoever only comes to ask for something", () => {
    user.current = { id: 7, role: "GUEST" };
    pathname.current = "/requests";

    draw();

    expect(screen.queryByRole("navigation")).toBeNull();
    expect(screen.getByText("L'écran")).toBeInTheDocument();
  });

  it("asks nobody for their mood but the team", () => {
    // The moods are a mirror the team holds up to itself. Somebody who only
    // ever comes to ask for something is not in it, and would be answering
    // about an afternoon they did not spend here.
    user.current = { id: 7, role: "GUEST" };
    pathname.current = "/requests";

    draw();

    expect(screen.queryByText("Le rappel du moral")).toBeNull();
  });

  it("sends a guest back to their own screen", () => {
    user.current = { id: 7, role: "GUEST" };
    pathname.current = "/timesheet";

    draw();

    expect(replace).toHaveBeenCalledWith("/requests");
    // Nothing of the screen they were heading for is drawn on the way.
    expect(screen.queryByText("L'écran")).toBeNull();
  });

  it("draws nothing until it knows who is there", () => {
    user.current = null;
    user.isLoading = true;

    draw();

    expect(screen.queryByRole("navigation")).toBeNull();
    expect(screen.queryByText("L'écran")).toBeNull();
  });
});
