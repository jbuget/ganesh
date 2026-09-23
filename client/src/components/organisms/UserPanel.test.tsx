import { beforeEach, describe, expect, it, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import type { UserResponse } from "@/lib/api/generated/model";

import { UserPanel } from "./UserPanel";
import { A_WEEK_ON_SITE } from "@/lib/presence";

/**
 * The three facets have their own tests: what is asked here is that the panel
 * puts them where it says, and that it opens on the one it says.
 */
vi.mock("@/components/organisms/UserActivityTab", () => ({
  UserActivityTab: ({ userId }: { userId: number }) => <div>Activité de {userId}</div>,
}));
vi.mock("@/components/organisms/UserAuditTab", () => ({
  UserAuditTab: ({ userId }: { userId: number }) => <div>Journal de {userId}</div>,
}));

const jeremy: UserResponse = {
  id: 1,
  email: "j.buget@waat.fr",
  display_name: "Jérémy Buget",
  initials: "JB",
  role: "MANAGER",
  presence: A_WEEK_ON_SITE,
  reminder_cadence: "DAILY",
  is_active: true,
  last_login_at: "2026-09-17T07:00:00Z",
};

const NOW = new Date("2026-09-17T10:00:00Z");

const onChangeRole = vi.fn();
const onUpdateIdentity = vi.fn();
const onSetActive = vi.fn();
const onDeclarePresence = vi.fn();
const onClose = vi.fn();

function openPanel({ canChangeStatus = false } = {}) {
  render(
    <UserPanel
      user={jeremy}
      roleModifiable={false}
      canChangeStatus={canChangeStatus}
      editable={false}
      onChangeRole={onChangeRole}
      onSetActive={onSetActive}
      onUpdateIdentity={onUpdateIdentity}
      isMe={false}
      onDeclarePresence={onDeclarePresence}
      now={NOW}
      onClose={onClose}
    />,
  );
}

/** Opens one of the three facets, the panel opening on the first. */
function openTab(name: string) {
  return userEvent.click(screen.getByRole("tab", { name }));
}

describe("UserPanel", () => {
  beforeEach(() => {
    onChangeRole.mockClear();
    onUpdateIdentity.mockClear();
    onSetActive.mockClear();
    onClose.mockClear();
  });

  it("names the teammate it was opened on", () => {
    openPanel();

    expect(
      screen.getByRole("complementary", { name: "Jérémy Buget" }),
    ).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Jérémy Buget" })).toBeInTheDocument();
  });

  /**
   * Three facets, and the account first: one opens a colleague to find out who
   * they are far more often than to read back what they did.
   */
  it("opens on the account, the two others waiting behind", () => {
    openPanel();

    expect(screen.getByRole("tab", { name: "Informations" })).toHaveAttribute(
      "aria-selected",
      "true",
    );
    expect(screen.getByRole("heading", { name: "Compte" })).toBeInTheDocument();
    expect(screen.queryByText("Activité de 1")).toBeNull();
    expect(screen.queryByText("Journal de 1")).toBeNull();
  });

  it("gives what the teammate carries a facet of its own", async () => {
    openPanel();

    await openTab("Activité");

    expect(screen.getByText("Activité de 1")).toBeInTheDocument();
  });

  it("gives the register a facet of its own", async () => {
    openPanel();

    await openTab("Journal");

    expect(screen.getByText("Journal de 1")).toBeInTheDocument();
  });

  /**
   * Escape closes the panel; the confirmation opens over it. Without care,
   * one press would answer both — the dialog would close and take the panel
   * with it.
   */
  it("gives Escape to the confirmation alone while it is open", async () => {
    openPanel({ canChangeStatus: true });
    await userEvent.click(screen.getByRole("button", { name: "Désactiver ce compte" }));

    await userEvent.keyboard("{Escape}");

    expect(screen.queryByRole("alertdialog")).toBeNull();
    expect(onClose).not.toHaveBeenCalled();
  });

  it("closes on Escape", async () => {
    openPanel();

    await userEvent.keyboard("{Escape}");

    expect(onClose).toHaveBeenCalledTimes(1);
  });

  it("closes on the cross", async () => {
    openPanel();

    await userEvent.click(screen.getByRole("button", { name: "Fermer" }));

    expect(onClose).toHaveBeenCalledTimes(1);
  });

  it("leads to that teammate's own month", () => {
    openPanel();

    expect(
      screen.getByRole("link", { name: "Ouvrir sa feuille de temps" }),
    ).toHaveAttribute("href", "/timesheet?user=1");
  });
});
