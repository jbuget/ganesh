import { describe, expect, it, vi } from "vitest";
import { render, screen } from "@testing-library/react";

import { UserMenu } from "./UserMenu";
import type { UserResponse } from "@/lib/api/generated/model";

/**
 * The menu rests on Base UI's Popover, which does not open under jsdom: its
 * content — full name, address, role, sign out — is checked in the browser.
 * What follows covers what the sidebar shows at all times.
 */
const USER: UserResponse = {
  id: 1,
  email: "j.buget@waat.fr",
  display_name: "Jérémy Buget",
  initials: "JB",
  role: "MANAGER",
  is_active: true,
} as UserResponse;

describe("UserMenu", () => {
  it("shows the name and initials of the signed-in person", () => {
    render(<UserMenu user={USER} onSignOut={vi.fn()} />);

    expect(screen.getByText("Jérémy Buget")).toBeInTheDocument();
    expect(screen.getByText("JB")).toBeInTheDocument();
  });

  it("announces what the menu opens", () => {
    render(<UserMenu user={USER} onSignOut={vi.fn()} />);

    expect(screen.getByRole("button", { name: /Jérémy Buget/ })).toBeInTheDocument();
  });

  it("flags the manager role under the name", () => {
    render(<UserMenu user={USER} onSignOut={vi.fn()} />);

    expect(screen.getByText("Manager")).toBeInTheDocument();
  });

  it("shows no role under a teammate's name", () => {
    render(<UserMenu user={{ ...USER, role: "TEAMMATE" }} onSignOut={vi.fn()} />);

    expect(screen.queryByText("Collaborateur")).toBeNull();
  });

  it("shrinks the block to initials when the bar is folded", () => {
    render(<UserMenu user={USER} onSignOut={vi.fn()} collapsed />);

    // The name leaves the eye, never the accessibility tree.
    expect(screen.getByRole("button", { name: /Jérémy Buget/ })).toBeInTheDocument();
    expect(screen.getByText("JB")).toBeInTheDocument();
  });
});
