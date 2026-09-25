import { beforeEach, describe, expect, it, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import type { UserResponse } from "@/lib/api/generated/model";
import { NAMING_COLUMN } from "@/lib/table-frame";
import { NO_USER_SORT } from "@/lib/user-sort";

import { UsersTable } from "./UsersTable";
import { A_WEEK_ON_SITE } from "@/lib/presence";

const TEAM: UserResponse[] = [
  {
    id: 1,
    email: "j.buget@waat.fr",
    display_name: "Jérémy Buget",
    initials: "JB",
    role: "MANAGER",
    presence: A_WEEK_ON_SITE,
    reminder_cadence: "DAILY",
    is_active: true,
    last_login_at: "2026-09-17T07:00:00Z",
    github_username: "jbuget",
  },
  {
    id: 2,
    email: "l.chen@waat.fr",
    display_name: "L. Chen",
    initials: "LC",
    role: "TEAMMATE",
    presence: A_WEEK_ON_SITE,
    reminder_cadence: "DAILY",
    is_active: true,
    last_login_at: null,
  },
];

const NOW = new Date("2026-09-17T12:00:00");
const onOpen = vi.fn();
const onSort = vi.fn();

function renderTable(users: UserResponse[] = TEAM) {
  return render(
    <UsersTable
      users={users}
      sorted={NO_USER_SORT}
      onSort={onSort}
      now={NOW}
      onOpen={onOpen}
    />,
  );
}

describe("UsersTable", () => {
  beforeEach(() => {
    onOpen.mockClear();
    onSort.mockClear();
  });

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

  it("asks for a column to sort by when its title is clicked", () => {
    renderTable();

    return userEvent
      .click(screen.getByRole("button", { name: "Dernière connexion" }))
      .then(() => expect(onSort).toHaveBeenCalledWith("login"));
  });

  it("says which column arranges the list, and which way round", () => {
    render(
      <UsersTable
        users={TEAM}
        sorted={{ column: "role", direction: "desc" }}
        onSort={onSort}
        now={NOW}
        onOpen={onOpen}
      />,
    );

    expect(screen.getByRole("columnheader", { name: /Rôle/ })).toHaveAttribute(
      "aria-sort",
      "descending",
    );
    expect(screen.getByRole("columnheader", { name: "Email" })).toHaveAttribute(
      "aria-sort",
      "none",
    );
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

describe("the naming column", () => {
  it("is as wide as it is on the presence tab", () => {
    // Held in `table-frame` so the two cannot drift: the accounts and the week
    // are read one after the other, and the column that names the row must not
    // move between them.
    renderTable();

    const header = screen.getByRole("columnheader", { name: /Collaborateur/ });
    expect(header.className).toContain(NAMING_COLUMN);
  });
});
