import { beforeEach, describe, expect, it, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import type { UserResponse } from "@/lib/api/generated/model";

import { UsersTable } from "./UsersTable";

const TEAM: UserResponse[] = [
  {
    id: 1,
    email: "j.buget@waat.fr",
    display_name: "Jérémy Buget",
    initials: "JB",
    role: "MANAGER",
    is_active: true,
    last_login_at: "2026-09-17T09:00:00",
    github_username: "jbuget",
  },
  {
    id: 2,
    email: "l.chen@waat.fr",
    display_name: "L. Chen",
    initials: "LC",
    role: "TEAMMATE",
    is_active: true,
    last_login_at: null,
  },
];

const NOW = new Date("2026-09-17T12:00:00");
const onOpen = vi.fn();

function renderTable(users: UserResponse[] = TEAM) {
  return render(<UsersTable users={users} now={NOW} onOpen={onOpen} />);
}

describe("UsersTable", () => {
  beforeEach(() => onOpen.mockClear());

  it("names the columns one compares the team under", () => {
    renderTable();

    for (const title of [
      "Collaborateur",
      "Email",
      "GitHub",
      "Rôle",
      "Dernière connexion",
      "Statut",
    ]) {
      expect(screen.getByRole("columnheader", { name: title })).toBeInTheDocument();
    }
  });

  it("draws one row per teammate, in the order it is given", () => {
    renderTable();

    expect(screen.getByText("Jérémy Buget")).toBeInTheDocument();
    expect(screen.getByText("L. Chen")).toBeInTheDocument();
  });

  it("names the GitHub handle, and marks the accounts that have none", () => {
    renderTable();

    expect(screen.getByText("jbuget")).toBeInTheDocument();
    expect(screen.getByText("—")).toBeInTheDocument();
  });

  it("opens the teammate a row names", async () => {
    renderTable();

    await userEvent.click(screen.getByText("L. Chen"));

    expect(onOpen).toHaveBeenCalledWith(2);
  });

  it("closes the column naming the teammate with a strong rule", () => {
    // The same boundary as the reference list: what identifies a row is told
    // apart from what describes it.
    renderTable();

    expect(screen.getByRole("columnheader", { name: "Collaborateur" })).toHaveClass(
      "border-r-slate-500",
    );
  });
});
