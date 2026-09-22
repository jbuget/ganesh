import { describe, expect, it } from "vitest";

import type { UserResponse } from "@/lib/api/generated/model";
import {
  NO_USER_FILTER,
  hiddenRequesters,
  withRequesters,
  filterUsers,
  hasActiveUserFilter,
  readUserFilters,
  writeUserFilters,
} from "@/lib/user-filters";

const teammate = (
  display_name: string,
  fields: Partial<UserResponse> = {},
): UserResponse => ({
  id: display_name.length,
  email: `${display_name.toLowerCase().replace(/\s/g, ".")}@waat.fr`,
  display_name,
  initials: display_name.slice(0, 2).toUpperCase(),
  role: "TEAMMATE",
  is_active: true,
  last_login_at: null,
  ...fields,
});

const names = (users: UserResponse[]) => users.map((user) => user.display_name);

describe("filterUsers", () => {
  it("keeps everyone whose access is open when nothing is asked", () => {
    const team = [teammate("Zoé"), teammate("Partie", { is_active: false })];

    expect(names(filterUsers(team, NO_USER_FILTER))).toEqual(["Zoé"]);
  });

  it("brings up the deactivated accounts when they are asked for", () => {
    const team = [teammate("Zoé"), teammate("Partie", { is_active: false })];

    expect(
      names(filterUsers(team, { ...NO_USER_FILTER, states: ["inactive"] })),
    ).toEqual(["Partie"]);
    expect(
      names(filterUsers(team, { ...NO_USER_FILTER, states: ["active", "inactive"] })),
    ).toEqual(["Zoé", "Partie"]);
  });

  it("searches the name without minding the accents nor the case", () => {
    const team = [teammate("Jérémy Buget"), teammate("Adrien")];

    expect(names(filterUsers(team, { ...NO_USER_FILTER, name: "jeremy" }))).toEqual([
      "Jérémy Buget",
    ]);
  });

  it("searches the email too: one looks a colleague up by either", () => {
    const team = [teammate("Jérémy Buget"), teammate("Adrien")];

    expect(names(filterUsers(team, { ...NO_USER_FILTER, name: "adrien@" }))).toEqual([
      "Adrien",
    ]);
  });

  it("keeps the roles asked for", () => {
    const team = [teammate("Chef", { role: "MANAGER" }), teammate("Zoé")];

    expect(names(filterUsers(team, { ...NO_USER_FILTER, roles: ["MANAGER"] }))).toEqual(
      ["Chef"],
    );
  });

  it("leaves out whoever only ever came to file a need", () => {
    const team = [
      teammate("Chef", { role: "MANAGER" }),
      teammate("Métier", {
        role: "REQUESTER",
      }),
    ];

    expect(names(filterUsers(team, NO_USER_FILTER))).toEqual(["Chef"]);
  });

  it("shows the requesters once they are asked for", () => {
    const team = [
      teammate("Chef", { role: "MANAGER" }),
      teammate("Métier", {
        role: "REQUESTER",
      }),
    ];

    expect(
      names(filterUsers(team, { ...NO_USER_FILTER, roles: ["REQUESTER"] })),
    ).toEqual(["Métier"]);
  });

  it("stacks the criteria: a manager whose name is searched", () => {
    const team = [
      teammate("Chef", { role: "MANAGER" }),
      teammate("Chèvre", { role: "TEAMMATE" }),
      teammate("Autre", { role: "MANAGER" }),
    ];

    expect(
      names(filterUsers(team, { ...NO_USER_FILTER, name: "che", roles: ["MANAGER"] })),
    ).toEqual(["Chef"]);
  });
});

describe("hasActiveUserFilter", () => {
  it("says nothing is set on an untouched bar", () => {
    expect(hasActiveUserFilter(NO_USER_FILTER)).toBe(false);
    expect(hasActiveUserFilter({ ...NO_USER_FILTER, name: "   " })).toBe(false);
  });

  it("says a criterion is set as soon as one is", () => {
    expect(hasActiveUserFilter({ ...NO_USER_FILTER, roles: ["MANAGER"] })).toBe(true);
    expect(hasActiveUserFilter({ ...NO_USER_FILTER, states: ["inactive"] })).toBe(true);
  });
});

describe("readUserFilters", () => {
  it("reads the criteria the address carries", () => {
    const params = new URLSearchParams("name=zo&role=MANAGER&state=inactive");

    expect(readUserFilters(params)).toEqual({
      name: "zo",
      roles: ["MANAGER"],
      states: ["inactive"],
    });
  });

  it("ignores a value it does not know rather than emptying the screen", () => {
    const params = new URLSearchParams("role=ADMIN&state=zombie");

    expect(readUserFilters(params)).toEqual(NO_USER_FILTER);
  });
});

describe("writeUserFilters", () => {
  it("writes the criteria without touching the other parameters", () => {
    const params = new URLSearchParams("user=3&sort=name");
    writeUserFilters(params, {
      name: " zo ",
      roles: ["MANAGER", "TEAMMATE"],
      states: ["inactive"],
    });

    expect(params.get("user")).toBe("3");
    expect(params.get("sort")).toBe("name");
    expect(params.get("name")).toBe("zo");
    expect(params.getAll("role")).toEqual(["MANAGER", "TEAMMATE"]);
    expect(params.getAll("state")).toEqual(["inactive"]);
  });

  it("takes the criteria out of the address when they are cleared", () => {
    const params = new URLSearchParams("name=zo&role=MANAGER&state=inactive");
    writeUserFilters(params, NO_USER_FILTER);

    expect(params.toString()).toBe("");
  });
});

describe("the requesters the list keeps out of sight", () => {
  const team = [
    teammate("Chef", { role: "MANAGER" }),
    teammate("Métier", { role: "REQUESTER" }),
    teammate("Compta", { role: "REQUESTER" }),
  ];

  it("counts what one more click would bring", () => {
    expect(hiddenRequesters(team, NO_USER_FILTER)).toBe(2);
  });

  it("counts nothing once they are asked for", () => {
    expect(hiddenRequesters(team, { ...NO_USER_FILTER, roles: ["REQUESTER"] })).toBe(0);
  });

  it("counts only those the other criteria would keep", () => {
    // A figure promising rows a search would still hide is a figure that lies.
    expect(hiddenRequesters(team, { ...NO_USER_FILTER, name: "compta" })).toBe(1);
  });

  it("shows them beside the team rather than instead of it", () => {
    const shown = filterUsers(team, withRequesters(NO_USER_FILTER));

    expect(names(shown)).toEqual(["Chef", "Métier", "Compta"]);
  });

  it("adds them to a criterion already set", () => {
    const shown = filterUsers(
      team,
      withRequesters({ ...NO_USER_FILTER, roles: ["MANAGER"] }),
    );

    expect(names(shown)).toEqual(["Chef", "Métier", "Compta"]);
  });
});
