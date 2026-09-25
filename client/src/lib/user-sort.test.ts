import { describe, expect, it } from "vitest";

import type { UserResponse } from "@/lib/api/generated/model";
import {
  NO_USER_SORT,
  nextUserSort,
  readUserSort,
  sortUsers,
  writeUserSort,
  type UserSort,
} from "@/lib/user-sort";
import { A_WEEK_ON_SITE } from "@/lib/presence";

const teammate = (
  display_name: string,
  fields: Partial<UserResponse> = {},
): UserResponse => ({
  id: display_name.length,
  email: `${display_name.toLowerCase().replace(/\s/g, ".")}@waat.fr`,
  display_name,
  initials: display_name.slice(0, 2).toUpperCase(),
  role: "TEAMMATE",
  presence: A_WEEK_ON_SITE,
  reminder_cadence: "DAILY",
  is_active: true,
  last_login_at: null,
  ...fields,
});

const names = (users: UserResponse[]) => users.map((user) => user.display_name);

describe("sortUsers", () => {
  it("falls back on the name, the only order one finds by eye", () => {
    const team = [teammate("Zoé"), teammate("Élodie"), teammate("Adrien")];

    expect(names(sortUsers(team, NO_USER_SORT))).toEqual(["Adrien", "Élodie", "Zoé"]);
  });

  it("orders by role, from the least to the most empowered", () => {
    const team = [
      teammate("Adrien", { role: "MANAGER" }),
      teammate("Zoé", { role: "TEAMMATE" }),
    ];

    expect(names(sortUsers(team, { column: "role", direction: "asc" }))).toEqual([
      "Zoé",
      "Adrien",
    ]);
    expect(names(sortUsers(team, { column: "role", direction: "desc" }))).toEqual([
      "Adrien",
      "Zoé",
    ]);
  });

  it("orders by last login, the oldest first", () => {
    const team = [
      teammate("Récent", { last_login_at: "2026-09-18T09:00:00" }),
      teammate("Ancien", { last_login_at: "2026-01-04T09:00:00" }),
    ];

    expect(names(sortUsers(team, { column: "login", direction: "asc" }))).toEqual([
      "Ancien",
      "Récent",
    ]);
  });

  it("leaves an account that never came at the end, whichever way round", () => {
    // « Jamais » is not « long ago »: it does not compare, so it waits at the
    // end rather than taking the top of a descending sort.
    const team = [
      teammate("Jamais"),
      teammate("Venu", { last_login_at: "2026-09-18T09:00:00" }),
    ];

    expect(names(sortUsers(team, { column: "login", direction: "asc" }))).toEqual([
      "Venu",
      "Jamais",
    ]);
    expect(names(sortUsers(team, { column: "login", direction: "desc" }))).toEqual([
      "Venu",
      "Jamais",
    ]);
  });

  it("settles a tie by the name, so the order does not drift between renders", () => {
    const team = [
      teammate("Zoé", { role: "MANAGER" }),
      teammate("Adrien", { role: "MANAGER" }),
    ];

    expect(names(sortUsers(team, { column: "role", direction: "desc" }))).toEqual([
      "Adrien",
      "Zoé",
    ]);
  });

  it("leaves a teammate with no GitHub handle at the end, whichever way round", () => {
    // The row shows « — » there: an absence, not a name that sorts last.
    const team = [teammate("Sans"), teammate("Avec", { github_username: "avec" })];

    expect(names(sortUsers(team, { column: "github", direction: "asc" }))).toEqual([
      "Avec",
      "Sans",
    ]);
    expect(names(sortUsers(team, { column: "github", direction: "desc" }))).toEqual([
      "Avec",
      "Sans",
    ]);
  });

  it("orders by status, open access first", () => {
    const team = [teammate("Partie", { is_active: false }), teammate("Présente")];

    expect(names(sortUsers(team, { column: "status", direction: "asc" }))).toEqual([
      "Présente",
      "Partie",
    ]);
  });

  it("leaves the list it is given alone", () => {
    const team = [teammate("Zoé"), teammate("Adrien")];
    sortUsers(team, NO_USER_SORT);

    expect(names(team)).toEqual(["Zoé", "Adrien"]);
  });
});

describe("nextUserSort", () => {
  it("cycles ascending, descending, then the list's own order", () => {
    let sorted: UserSort = NO_USER_SORT;

    sorted = nextUserSort(sorted, "email");
    expect(sorted).toEqual({ column: "email", direction: "asc" });

    sorted = nextUserSort(sorted, "email");
    expect(sorted).toEqual({ column: "email", direction: "desc" });

    sorted = nextUserSort(sorted, "email");
    expect(sorted).toEqual(NO_USER_SORT);
  });

  it("starts a new column ascending", () => {
    const sorted = nextUserSort({ column: "email", direction: "desc" }, "role");

    expect(sorted).toEqual({ column: "role", direction: "asc" });
  });
});

describe("readUserSort", () => {
  it("reads the column and the direction the address carries", () => {
    const params = new URLSearchParams("sort=login&direction=desc");

    expect(readUserSort(params)).toEqual({ column: "login", direction: "desc" });
  });

  it("ignores a column it does not know", () => {
    expect(readUserSort(new URLSearchParams("sort=département"))).toEqual(NO_USER_SORT);
  });
});

describe("writeUserSort", () => {
  it("writes the sort without touching the other parameters", () => {
    const params = new URLSearchParams("user=3&role=MANAGER");
    writeUserSort(params, { column: "name", direction: "desc" });

    expect(params.get("user")).toBe("3");
    expect(params.get("role")).toBe("MANAGER");
    expect(params.get("sort")).toBe("name");
    expect(params.get("direction")).toBe("desc");
  });

  it("takes the sort out of the address when the list keeps its own order", () => {
    const params = new URLSearchParams("sort=name&direction=desc");
    writeUserSort(params, NO_USER_SORT);

    expect(params.toString()).toBe("");
  });
});
