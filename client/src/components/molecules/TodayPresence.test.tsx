import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { TodayPresence } from "@/components/molecules/TodayPresence";
import type { UserResponse } from "@/lib/api/generated/model";
import { A_WEEK_ON_SITE } from "@/lib/presence";

// Wednesday 23 September 2026, and the Saturday that follows it.
const WEDNESDAY = new Date(2026, 8, 23);
const SATURDAY = new Date(2026, 8, 26);

function aUser(
  id: number,
  display_name: string,
  presence: UserResponse["presence"] = A_WEEK_ON_SITE,
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

const away = { ...A_WEEK_ON_SITE, wednesday: "AWAY" } as const;
const remote = { ...A_WEEK_ON_SITE, wednesday: "REMOTE" } as const;

describe("who is in", () => {
  it("counts the three places apart", () => {
    render(
      <TodayPresence
        today={WEDNESDAY}
        users={[aUser(1, "Léa"), aUser(2, "Malik", remote), aUser(3, "Nour", away)]}
      />,
    );

    expect(screen.getByText(/sur site/)).toHaveTextContent("1 sur site");
    expect(screen.getByText(/en télétravail/)).toHaveTextContent("1 en télétravail");
    expect(screen.getByText(/absent/)).toHaveTextContent("1 absent");
  });

  it("shows the faces of those in, because a figure says how many, not who", () => {
    render(<TodayPresence today={WEDNESDAY} users={[aUser(1, "Léa")]} />);

    // Named, not only drawn: the faces are the whole answer here.
    expect(screen.getByText("Léa")).toBeInTheDocument();
    expect(screen.getByTitle("Léa")).toBeInTheDocument();
  });

  it("says nothing of an absence nobody has", () => {
    render(<TodayPresence today={WEDNESDAY} users={[aUser(1, "Léa")]} />);

    expect(screen.queryByText(/absent/)).not.toBeInTheDocument();
  });
});

describe("the day it reads", () => {
  it("says « Aujourd'hui » on a working day", () => {
    render(<TodayPresence today={WEDNESDAY} users={[aUser(1, "Léa")]} />);

    expect(screen.getByRole("heading", { name: "Aujourd'hui" })).toBeInTheDocument();
  });

  it("reads Monday at the weekend, and names it", () => {
    // « Qui est là aujourd'hui » answers nothing on a Saturday.
    render(<TodayPresence today={SATURDAY} users={[aUser(1, "Léa", away)]} />);

    expect(screen.getByRole("heading", { name: "Lundi" })).toBeInTheDocument();
    expect(screen.getByText(/sur site/)).toHaveTextContent("1 sur site");
  });
});

describe("handing over", () => {
  it("opens the week on the tab that holds it", () => {
    render(<TodayPresence today={WEDNESDAY} users={[aUser(1, "Léa")]} />);

    expect(screen.getByRole("link", { name: "Toute la semaine" })).toHaveAttribute(
      "href",
      "/users?vue=presence",
    );
  });

  it("draws nothing at all before the team has loaded", () => {
    const { container } = render(<TodayPresence today={WEDNESDAY} users={[]} />);

    expect(container).toBeEmptyDOMElement();
  });
});
