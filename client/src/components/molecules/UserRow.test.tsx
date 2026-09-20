import { beforeEach, describe, expect, it, vi } from "vitest";
import { cleanup, render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import { Table, TableBody } from "@/components/ui/table";
import type { UserResponse } from "@/lib/api/generated/model";

import { UserRow } from "./UserRow";

const jeremy: UserResponse = {
  id: 1,
  email: "j.buget@waat.fr",
  display_name: "Jérémy Buget",
  initials: "JB",
  role: "MANAGER",
  is_active: true,
};

const NOW = new Date("2026-09-17T10:00:00Z");

const onOpen = vi.fn();

function renderRow(user: UserResponse) {
  return render(
    <Table>
      <TableBody>
        <UserRow user={user} now={NOW} onOpen={onOpen} />
      </TableBody>
    </Table>,
  );
}

describe("UserRow", () => {
  beforeEach(() => onOpen.mockClear());

  it("shows the teammate, their email and their role", () => {
    renderRow(jeremy);

    expect(screen.getByText("Jérémy Buget")).toBeInTheDocument();
    expect(screen.getByText("j.buget@waat.fr")).toBeInTheDocument();
    expect(screen.getByText("Manager")).toBeInTheDocument();
  });

  it("names the status in both cases", () => {
    renderRow(jeremy);
    expect(screen.getByText("Actif")).toBeInTheDocument();

    cleanup();
    renderRow({ ...jeremy, is_active: false });
    expect(screen.getByText("Désactivé")).toBeInTheDocument();
  });

  it("opens the panel rather than editing in place", async () => {
    renderRow(jeremy);

    await userEvent.click(screen.getByText("Jérémy Buget"));

    expect(onOpen).toHaveBeenCalledTimes(1);
  });

  it("edits nothing: the role and the access are given away in the panel", () => {
    renderRow(jeremy);

    expect(screen.queryByRole("button", { name: /Changer le rôle/ })).toBeNull();
    expect(screen.queryByRole("button", { name: /Désactiver/ })).toBeNull();
  });

  it("says how long since the account last logged in", () => {
    renderRow({ ...jeremy, last_login_at: "2026-09-17T07:00:00Z" });

    expect(screen.getByText("il y a 3 h")).toBeInTheDocument();
  });

  it("tells apart an account that has never logged in", () => {
    renderRow({ ...jeremy, last_login_at: null });

    expect(screen.getByText("Jamais")).toBeInTheDocument();
  });
});
