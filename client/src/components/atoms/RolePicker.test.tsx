import { describe, expect, it, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import type { Role } from "@/lib/api/generated/model";

import { RolePicker } from "./RolePicker";

/** What an admin may hand out: every rung of the ladder. */
const ALL: Role[] = ["GUEST", "TEAMMATE", "MANAGER", "ADMIN"];

describe("RolePicker", () => {
  it("shows the current role", () => {
    render(<RolePicker role="MANAGER" choices={ALL} onChange={vi.fn()} />);

    expect(screen.getByRole("button", { name: /Manager/ })).toBeInTheDocument();
  });

  it("offers no button when there is no role to hand out", () => {
    render(<RolePicker role="TEAMMATE" choices={[]} onChange={vi.fn()} />);

    expect(screen.getByText("Collaborateur")).toBeInTheDocument();
    expect(screen.queryByRole("button")).toBeNull();
  });

  it("changes the role when another is chosen", async () => {
    const onChange = vi.fn();
    render(<RolePicker role="TEAMMATE" choices={ALL} onChange={onChange} />);

    await userEvent.click(screen.getByRole("button", { name: /Collaborateur/ }));
    await userEvent.click(screen.getByRole("button", { name: /Manager/ }));

    expect(onChange).toHaveBeenCalledWith("MANAGER");
  });

  it("does not replay the role already held", async () => {
    const onChange = vi.fn();
    render(<RolePicker role="MANAGER" choices={ALL} onChange={onChange} />);

    await userEvent.click(screen.getByRole("button", { name: /Manager/ }));
    await userEvent.click(
      screen.getAllByRole("button", { name: /Manager/ }).at(-1) as HTMLElement,
    );

    expect(onChange).not.toHaveBeenCalled();
  });
});

describe("RolePicker, bounded", () => {
  it("offers only what the reader may hand out", async () => {
    render(
      <RolePicker
        role="TEAMMATE"
        choices={["GUEST", "TEAMMATE", "MANAGER"]}
        onChange={vi.fn()}
      />,
    );

    await userEvent.click(screen.getByRole("button", { name: /Collaborateur/ }));

    expect(screen.getByRole("button", { name: /Manager/ })).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: /Administrateur/ })).toBeNull();
  });
});
