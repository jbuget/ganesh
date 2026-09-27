import { describe, expect, it, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import type { UserResponse } from "@/lib/api/generated/model";
import { A_WEEK_ON_SITE } from "@/lib/presence";

import { ReadAsAccount } from "./ReadAsAccount";

const me = vi.hoisted(() => ({
  current: { id: 1, role: "ADMIN", impersonated_by: null } as Record<string, unknown>,
}));
const readAs = vi.hoisted(() => vi.fn(async () => null as string | null));
const borrowing = vi.hoisted(() => ({ value: false }));

vi.mock("@/lib/api/queries", () => ({ useCurrentUser: () => ({ user: me.current }) }));
vi.mock("@/lib/use-read-as", () => ({
  useReadAs: () => ({
    readAs,
    isMoving: false,
    isBorrowing: borrowing.value,
  }),
}));

const chen: UserResponse = {
  id: 2,
  email: "l.chen@waat.fr",
  display_name: "L. Chen",
  initials: "LC",
  role: "TEAMMATE",
  presence: A_WEEK_ON_SITE,
  reminder_cadence: "DAILY",
  is_active: true,
};

function draw(user: Partial<UserResponse> = {}) {
  return render(<ReadAsAccount user={{ ...chen, ...user }} />);
}

/**
 * What shows here must be exactly what `read_as` would accept: an offer the
 * API refuses is a refusal somebody meets by clicking.
 */
describe("ReadAsAccount", () => {
  it("offers an administrator a teammate's screens, by name", () => {
    me.current = { id: 1, role: "ADMIN" };
    borrowing.value = false;
    draw();

    expect(screen.getByRole("button", { name: /L\. Chen/ })).toBeInTheDocument();
  });

  it("says that nothing can be entered from inside the account", () => {
    // An administrator who expected to fill a month in from there would find
    // out by clicking, on a refusal, three screens later.
    me.current = { id: 1, role: "ADMIN" };
    borrowing.value = false;
    draw();

    expect(screen.getByText(/sans rien pouvoir y saisir/)).toBeInTheDocument();
  });

  it.each(["MANAGER", "TEAMMATE", "GUEST"])("offers nothing to a %s", (role) => {
    me.current = { id: 1, role };
    borrowing.value = false;
    const { container } = draw();

    expect(container).toBeEmptyDOMElement();
  });

  it("offers nothing on one's own account", () => {
    me.current = { id: 2, role: "ADMIN" };
    borrowing.value = false;
    const { container } = draw();

    expect(container).toBeEmptyDOMElement();
  });

  it("offers nothing on an account whose access was cut off", () => {
    // Behind a closed door there is no screen to go and look at.
    me.current = { id: 1, role: "ADMIN" };
    borrowing.value = false;
    const { container } = draw({ is_active: false });

    expect(container).toBeEmptyDOMElement();
  });

  it("offers nothing to somebody already reading as somebody else", () => {
    // Two bands would say two different names over the same screen.
    me.current = { id: 1, role: "ADMIN" };
    borrowing.value = true;
    const { container } = draw();

    expect(container).toBeEmptyDOMElement();
  });

  it("shows what the API said when it refuses", async () => {
    me.current = { id: 1, role: "ADMIN" };
    borrowing.value = false;
    readAs.mockResolvedValueOnce("Ce compte est désactivé.");
    draw();

    await userEvent.click(screen.getByRole("button", { name: /L\. Chen/ }));

    expect(await screen.findByRole("alert")).toHaveTextContent(
      "Ce compte est désactivé.",
    );
  });
});
