import { describe, expect, it, vi } from "vitest";
import { fireEvent, render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import { UserFilters } from "./UserFilters";
import {
  NO_USER_FILTER,
  hasActiveUserFilter,
  type UserFilters as Criteria,
} from "@/lib/user-filters";

const bar = (over: Partial<Criteria> = {}) => {
  const filters = { ...NO_USER_FILTER, ...over };
  const onChange = vi.fn();
  const onClear = vi.fn();
  render(
    <UserFilters
      filters={filters}
      hasFilter={hasActiveUserFilter(filters)}
      onChange={onChange}
      onClear={onClear}
      visible={3}
      total={12}
    />,
  );
  return { onChange, onClear };
};

describe("UserFilters", () => {
  it("offers the three criteria", () => {
    bar();

    expect(screen.getByLabelText("Rechercher un collaborateur")).toBeInTheDocument();
    ["Rôle", "Statut"].forEach((criterion) => {
      expect(
        screen.getByRole("button", { name: new RegExp(criterion) }),
      ).toBeInTheDocument();
    });
  });

  it("passes on what is searched, without waiting for a confirmation", () => {
    const { onChange } = bar();

    fireEvent.change(screen.getByLabelText("Rechercher un collaborateur"), {
      target: { value: "zo" },
    });

    expect(onChange).toHaveBeenCalledWith({ name: "zo" });
  });

  it("ticks a role without closing the menu", async () => {
    const { onChange } = bar();

    await userEvent.click(screen.getByRole("button", { name: "Rôle" }));
    await userEvent.click(screen.getByRole("button", { name: "Manager" }));

    expect(onChange).toHaveBeenCalledWith({ roles: ["MANAGER"] });
  });

  it("says how many are seen out of how many, once a criterion is set", () => {
    bar({ roles: ["MANAGER"] });

    expect(screen.getByRole("status")).toHaveTextContent("3 collaborateurs sur 12");
  });

  it("keeps quiet about the count as long as nothing is filtered", () => {
    bar();

    expect(screen.queryByRole("status")).toBeNull();
  });

  it("offers clearing only what has been set", async () => {
    expect(screen.queryByRole("button", { name: /Effacer/ })).toBeNull();

    const { onClear } = bar({ states: ["inactive"] });
    await userEvent.click(screen.getByRole("button", { name: /Effacer/ }));

    expect(onClear).toHaveBeenCalledTimes(1);
  });
});
