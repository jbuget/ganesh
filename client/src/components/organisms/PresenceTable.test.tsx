import { render, screen, within } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { PresenceTable } from "@/components/organisms/PresenceTable";
import type { UserResponse } from "@/lib/api/generated/model";

function aUser(
  id: number,
  display_name: string,
  presence: UserResponse["presence"] = null,
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

  it("leaves a week nobody declared blank rather than drawing five absences", () => {
    // An office that merely looks empty would be read as an empty office.
    render(
      <PresenceTable users={[aUser(1, "Léa"), aUser(2, "Malik", AT_THE_OFFICE)]} />,
    );

    expect(screen.getByText("Lundi : non renseigné")).toBeInTheDocument();
    const footer = screen.getByRole("row", { name: /Sur site/ });
    expect(within(footer).getAllByRole("cell")[1]).toHaveTextContent("1sur 1 présent");
  });

  it("names each day of each week for whoever cannot see the marks", () => {
    render(
      <PresenceTable
        users={[aUser(1, "Léa", { ...AT_THE_OFFICE, friday: "REMOTE" })]}
      />,
    );

    expect(screen.getByText("Vendredi : télétravail")).toBeInTheDocument();
  });
});
