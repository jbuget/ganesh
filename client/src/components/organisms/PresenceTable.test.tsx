import { render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

import { PresenceTable } from "@/components/organisms/PresenceTable";
import type { UserResponse } from "@/lib/api/generated/model";
import { NAMING_COLUMN } from "@/lib/table-frame";
import { NO_USER_SORT } from "@/lib/user-sort";

function aUser(
  id: number,
  display_name: string,
  presence: UserResponse["presence"] = AT_THE_OFFICE,
): UserResponse {
  return {
    id,
    email: `${display_name}@waat.fr`,
    display_name,
    initials: display_name.slice(0, 2).toUpperCase(),
    role: "TEAMMATE",
    is_active: true,
    presence,
  };
}

const AT_THE_OFFICE = {
  monday: "ON_SITE",
  tuesday: "ON_SITE",
  wednesday: "ON_SITE",
  thursday: "ON_SITE",
  friday: "ON_SITE",
  days_on_site: 5,
  days_present: 5,
} as const;

describe("the week of the team", () => {
  it("counts who is on site under each day", () => {
    // The figure the screen is opened for.
    render(
      <PresenceTable
        sorted={NO_USER_SORT}
        onSort={vi.fn()}
        onOpen={vi.fn()}
        users={[
          aUser(1, "Léa", { ...AT_THE_OFFICE, wednesday: "REMOTE" }),
          aUser(2, "Malik", { ...AT_THE_OFFICE, wednesday: "AWAY" }),
        ]}
      />,
    );

    const footer = screen.getByRole("row", { name: /Sur site/ });
    const cells = within(footer).getAllByRole("cell");
    expect(cells[1]).toHaveTextContent("2sur 2 présents");
    expect(cells[3]).toHaveTextContent("0sur 1 présent");
  });

  it("counts everybody, since everybody has a week", () => {
    // On site every day until somebody says otherwise: nothing is ever blank,
    // so the count under each day covers the whole team.
    render(
      <PresenceTable
        sorted={NO_USER_SORT}
        onSort={vi.fn()}
        onOpen={vi.fn()}
        users={[aUser(1, "Léa"), aUser(2, "Malik")]}
      />,
    );

    const footer = screen.getByRole("row", { name: /Sur site/ });
    expect(within(footer).getAllByRole("cell")[1]).toHaveTextContent("2sur 2 présents");
  });

  it("names each day of each week for whoever cannot see the marks", () => {
    render(
      <PresenceTable
        sorted={NO_USER_SORT}
        onSort={vi.fn()}
        onOpen={vi.fn()}
        users={[aUser(1, "Léa", { ...AT_THE_OFFICE, friday: "REMOTE" })]}
      />,
    );

    expect(screen.getByText("Vendredi : télétravail")).toBeInTheDocument();
  });
});

describe("going from a week to the person", () => {
  it("opens the teammate the row names", async () => {
    // The two tabs are two readings of one list: a line means the same thing
    // in both, so it opens the same panel.
    const onOpen = vi.fn();
    render(
      <PresenceTable
        sorted={NO_USER_SORT}
        onSort={vi.fn()}
        onOpen={onOpen}
        users={[aUser(7, "Léa")]}
      />,
    );

    await userEvent.click(screen.getByText("Léa"));

    expect(onOpen).toHaveBeenCalledWith(7);
  });
});

describe("the same grammar as the accounts tab", () => {
  it("names the teammate through a button, as the accounts row does", () => {
    // Two readings of one list: the name is the anchor of the line in both,
    // it looks the same and it opens the same way — including by keyboard.
    render(
      <PresenceTable
        sorted={NO_USER_SORT}
        onSort={vi.fn()}
        onOpen={vi.fn()}
        users={[aUser(7, "Léa")]}
      />,
    );

    expect(screen.getByRole("button", { name: "Léa" })).toBeInTheDocument();
  });

  it("gives the naming column the width every table gives it", () => {
    // A name column that changed width between two tabs makes the whole page
    // shift under the reader for no reason at all.
    render(
      <PresenceTable
        sorted={NO_USER_SORT}
        onSort={vi.fn()}
        onOpen={vi.fn()}
        users={[aUser(7, "Léa")]}
      />,
    );

    const header = screen.getByRole("columnheader", { name: "Collaborateur" });
    expect(header.className).toContain(NAMING_COLUMN);
  });
});

describe("arranging the week", () => {
  it("sorts by the same column, and says so the same way", async () => {
    const onSort = vi.fn();
    render(
      <PresenceTable
        sorted={NO_USER_SORT}
        onSort={onSort}
        onOpen={vi.fn()}
        users={[aUser(1, "Léa"), aUser(2, "Malik")]}
      />,
    );

    // The whole cell answers the click, and a button inside it carries it.
    await userEvent.click(screen.getByRole("button", { name: /Collaborateur/ }));

    expect(onSort).toHaveBeenCalledWith("name");
  });
});
