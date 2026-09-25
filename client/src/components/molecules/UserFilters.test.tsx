import { describe, expect, it, vi } from "vitest";
import { fireEvent, render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import { UserFilters } from "./UserFilters";
import {
  NO_USER_FILTER,
  hasActiveUserFilter,
  type UserFilters as Criteria,
} from "@/lib/user-filters";

const bar = (over: Partial<Criteria> = {}, hidden = 0) => {
  const filters = { ...NO_USER_FILTER, ...over };
  const onChange = vi.fn();
  const onClear = vi.fn();
  const onShowRequesters = vi.fn();
  render(
    <UserFilters
      filters={filters}
      hasFilter={hasActiveUserFilter(filters)}
      onChange={onChange}
      onClear={onClear}
      visible={3}
      total={12}
      hidden={hidden}
      onShowRequesters={onShowRequesters}
    />,
  );
  return { onChange, onClear, onShowRequesters };
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

describe("what the list is not showing", () => {
  it("says how many requesters it keeps out of sight", () => {
    // Fifteen rows out of three hundred, with nothing said, is what makes
    // somebody look for an account they were never shown.
    bar({}, 312);

    expect(
      screen.getByRole("button", { name: "Afficher les 312 demandeurs" }),
    ).toBeInTheDocument();
  });

  it("agrees when there is only one", () => {
    bar({}, 1);

    expect(
      screen.getByRole("button", { name: "Afficher le demandeur" }),
    ).toBeInTheDocument();
  });

  it("says nothing when there is nothing to say", () => {
    bar({}, 0);

    expect(screen.queryByRole("button", { name: /demandeur/ })).toBeNull();
  });

  it("brings them into the list on a click", async () => {
    const { onShowRequesters } = bar({}, 312);

    await userEvent.click(
      screen.getByRole("button", { name: "Afficher les 312 demandeurs" }),
    );

    expect(onShowRequesters).toHaveBeenCalled();
  });
});
