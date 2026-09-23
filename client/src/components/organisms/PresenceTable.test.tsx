import { render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

import { PresenceTable } from "@/components/organisms/PresenceTable";
import type { UserResponse } from "@/lib/api/generated/model";

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
      <PresenceTable onOpen={vi.fn()} users={[aUser(1, "Léa"), aUser(2, "Malik")]} />,
    );

    const footer = screen.getByRole("row", { name: /Sur site/ });
    expect(within(footer).getAllByRole("cell")[1]).toHaveTextContent("2sur 2 présents");
  });

  it("names each day of each week for whoever cannot see the marks", () => {
    render(
      <PresenceTable
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
    render(<PresenceTable onOpen={onOpen} users={[aUser(7, "Léa")]} />);

    await userEvent.click(screen.getByText("Léa"));

    expect(onOpen).toHaveBeenCalledWith(7);
  });
});
