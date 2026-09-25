import { describe, expect, it, vi } from "vitest";
import { renderHook } from "@testing-library/react";

import type { UserResponse } from "@/lib/api/generated/model";
import { NO_USER_FILTER } from "@/lib/user-filters";
import { NO_USER_SORT } from "@/lib/user-sort";

import { useUsersScreen } from "./use-users";
import { A_WEEK_ON_SITE } from "@/lib/presence";

const teammate = (
  display_name: string,
  fields: Partial<UserResponse> = {},
): UserResponse => ({
  id: display_name.length,
  email: `${display_name.toLowerCase()}@waat.fr`,
  display_name,
  initials: display_name.slice(0, 2).toUpperCase(),
  role: "TEAMMATE",
  presence: A_WEEK_ON_SITE,
  reminder_cadence: "DAILY",
  is_active: true,
  last_login_at: null,
  ...fields,
});

const TEAM = [
  teammate("Adrien", { id: 1 }),
  teammate("Chef", { id: 2, role: "MANAGER" }),
  teammate("Partie", { id: 3, is_active: false }),
];

vi.mock("@tanstack/react-query", () => ({
  useQueryClient: () => ({ invalidateQueries: vi.fn() }),
}));

vi.mock("@/lib/api/queries", () => ({
  useCurrentUser: () => ({ user: { id: 1, role: "MANAGER" } }),
  useTeammates: () => ({ teammates: TEAM, isLoading: false }),
}));

describe("useUsersScreen", () => {
  it("shows the open accounts alone as long as nothing is asked", () => {
    const { result } = renderHook(() => useUsersScreen());

    expect(result.current.users.map((user) => user.display_name)).toEqual([
      "Adrien",
      "Chef",
    ]);
  });

  it("counts against what one would see with no criterion, not the whole table", () => {
    // « 1 sur 3 » would promise a row that clearing the filters does not bring
    // back: the deactivated account stays hidden until it is asked for.
    const { result } = renderHook(() =>
      useUsersScreen({ ...NO_USER_FILTER, roles: ["MANAGER"] }, NO_USER_SORT),
    );

    expect(result.current.visible).toBe(1);
    expect(result.current.total).toBe(2);
  });

  it("counts the deactivated accounts in once they are asked for", () => {
    const { result } = renderHook(() =>
      useUsersScreen(
        { ...NO_USER_FILTER, states: ["active", "inactive"], roles: ["MANAGER"] },
        NO_USER_SORT,
      ),
    );

    expect(result.current.total).toBe(3);
  });

  it("finds a teammate the panel opens on, deactivated or not", () => {
    const { result } = renderHook(() => useUsersScreen());

    expect(result.current.find(3)?.display_name).toBe("Partie");
  });
});
