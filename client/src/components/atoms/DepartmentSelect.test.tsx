import { beforeEach, describe, expect, it, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import { DepartmentSelect } from "./DepartmentSelect";

const onChange = vi.fn();

function select(value: "customer_service" | null, editable = true) {
  render(<DepartmentSelect value={value} editable={editable} onChange={onChange} />);
}

describe("DepartmentSelect", () => {
  beforeEach(() => onChange.mockClear());

  it("names the department under the same label as the missions", () => {
    select("customer_service");

    expect(screen.getByText("Service client")).toBeInTheDocument();
  });

  it("says nothing is known rather than showing an empty cell", () => {
    select(null);

    expect(screen.getByRole("button", { name: /département/i })).toBeInTheDocument();
  });

  it("offers the list the missions are filed under", async () => {
    select(null);

    await userEvent.click(screen.getByRole("button", { name: /département/i }));

    expect(screen.getByRole("button", { name: "Bailleurs" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Tertiaire" })).toBeInTheDocument();
  });

  it("chooses a department", async () => {
    select(null);

    await userEvent.click(screen.getByRole("button", { name: /département/i }));
    await userEvent.click(screen.getByRole("button", { name: "Bailleurs" }));

    expect(onChange).toHaveBeenCalledWith("landlords");
  });

  it("takes the department back off", async () => {
    select("customer_service");

    await userEvent.click(screen.getByRole("button", { name: /département/i }));
    await userEvent.click(screen.getByRole("button", { name: "Aucun" }));

    expect(onChange).toHaveBeenCalledWith(null);
  });

  it("reads without editing when the reader may not write", () => {
    select("customer_service", false);

    expect(screen.queryByRole("button")).toBeNull();
    expect(screen.getByText("Service client")).toBeInTheDocument();
  });
});
