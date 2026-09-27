import { describe, expect, it, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import { ImpersonationBanner } from "./ImpersonationBanner";

const me = vi.hoisted(() => ({ current: null as Record<string, unknown> | null }));
const borrower = vi.hoisted(() => ({
  current: null as { id: number; display_name: string } | null,
}));
const giveBack = vi.hoisted(() => vi.fn());

vi.mock("@/lib/api/queries", () => ({ useCurrentUser: () => ({ user: me.current }) }));
vi.mock("@/lib/use-read-as", () => ({
  useReadAs: () => ({ borrower: borrower.current, isMoving: false, giveBack }),
}));

describe("ImpersonationBanner", () => {
  it("says nothing to somebody reading their own account", () => {
    me.current = { display_name: "L. Chen" };
    borrower.current = null;
    const { container } = render(<ImpersonationBanner />);

    expect(container).toBeEmptyDOMElement();
  });

  it("names the account being read, and who is reading it", () => {
    // Two teammates' screens look alike: the name is what tells the reader
    // they opened the one they meant to.
    me.current = { display_name: "L. Chen" };
    borrower.current = { id: 1, display_name: "Jérémy Buget" };
    render(<ImpersonationBanner />);

    expect(screen.getByRole("status")).toHaveTextContent("L. Chen");
    expect(screen.getByRole("status")).toHaveTextContent("Jérémy Buget");
  });

  it("offers the way back wherever the reader happens to be", async () => {
    me.current = { display_name: "L. Chen" };
    borrower.current = { id: 1, display_name: "Jérémy Buget" };
    render(<ImpersonationBanner />);

    await userEvent.click(screen.getByRole("button", { name: /Quitter/ }));

    expect(giveBack).toHaveBeenCalled();
  });
});
