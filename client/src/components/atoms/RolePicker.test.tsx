import { describe, expect, it, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import { RolePicker } from "./RolePicker";

describe("RolePicker", () => {
  it("shows the current role", () => {
    render(<RolePicker role="MANAGER" modifiable onChange={vi.fn()} />);

    expect(screen.getByRole("button", { name: /Manager/ })).toBeInTheDocument();
  });

  it("offers no button when the role cannot be changed", () => {
    render(<RolePicker role="TEAMMATE" modifiable={false} onChange={vi.fn()} />);

    expect(screen.getByText("Collaborateur")).toBeInTheDocument();
    expect(screen.queryByRole("button")).toBeNull();
  });

  it("changes the role when another is chosen", async () => {
    const onChange = vi.fn();
    render(<RolePicker role="TEAMMATE" modifiable onChange={onChange} />);

    await userEvent.click(screen.getByRole("button", { name: /Collaborateur/ }));
    await userEvent.click(screen.getByRole("button", { name: /Manager/ }));

    expect(onChange).toHaveBeenCalledWith("MANAGER");
  });

  it("does not replay the role already held", async () => {
    const onChange = vi.fn();
    render(<RolePicker role="MANAGER" modifiable onChange={onChange} />);

    await userEvent.click(screen.getByRole("button", { name: /Manager/ }));
    await userEvent.click(
      screen.getAllByRole("button", { name: /Manager/ }).at(-1) as HTMLElement,
    );

    expect(onChange).not.toHaveBeenCalled();
  });
});
