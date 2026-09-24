import { describe, expect, it, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import { RolePicker } from "./RolePicker";

/** What a manager may hand out: everything up to their own rank. */
const UP_TO_MANAGER = ["GUEST", "TEAMMATE", "MANAGER"] as const;

describe("RolePicker", () => {
  it("shows the current role", () => {
    render(
      <RolePicker
        role="MANAGER"
        modifiable
        grantable={[...UP_TO_MANAGER]}
        onChange={vi.fn()}
      />,
    );

    expect(screen.getByRole("button", { name: /Manager/ })).toBeInTheDocument();
  });

  it("offers no button when the role cannot be changed", () => {
    render(
      <RolePicker
        role="TEAMMATE"
        modifiable={false}
        grantable={[...UP_TO_MANAGER]}
        onChange={vi.fn()}
      />,
    );

    expect(screen.getByText("Collaborateur")).toBeInTheDocument();
    expect(screen.queryByRole("button")).toBeNull();
  });

  it("changes the role when another is chosen", async () => {
    const onChange = vi.fn();
    render(
      <RolePicker
        role="TEAMMATE"
        modifiable
        grantable={[...UP_TO_MANAGER]}
        onChange={onChange}
      />,
    );

    await userEvent.click(screen.getByRole("button", { name: /Collaborateur/ }));
    await userEvent.click(screen.getByRole("button", { name: /Manager/ }));

    expect(onChange).toHaveBeenCalledWith("MANAGER");
  });

  it("does not replay the role already held", async () => {
    const onChange = vi.fn();
    render(
      <RolePicker
        role="MANAGER"
        modifiable
        grantable={[...UP_TO_MANAGER]}
        onChange={onChange}
      />,
    );

    await userEvent.click(screen.getByRole("button", { name: /Manager/ }));
    await userEvent.click(
      screen.getAllByRole("button", { name: /Manager/ }).at(-1) as HTMLElement,
    );

    expect(onChange).not.toHaveBeenCalled();
  });

  it("never offers a rank above the reader's own", async () => {
    render(
      <RolePicker
        role="TEAMMATE"
        modifiable
        grantable={[...UP_TO_MANAGER]}
        onChange={vi.fn()}
      />,
    );

    await userEvent.click(screen.getByRole("button", { name: /Collaborateur/ }));

    expect(screen.queryByRole("button", { name: /Administrateur/ })).toBeNull();
  });

  it("still shows the rank held, even when it may not be handed out", () => {
    render(
      <RolePicker
        role="ADMIN"
        modifiable
        grantable={[...UP_TO_MANAGER]}
        onChange={vi.fn()}
      />,
    );

    expect(screen.getByText("Administrateur")).toBeInTheDocument();
  });
});
