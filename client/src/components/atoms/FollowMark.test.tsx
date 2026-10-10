import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

import { FollowMark } from "./FollowMark";

describe("FollowMark", () => {
  it("shows nothing on a mission nobody follows, when it cannot be changed", () => {
    const { container } = render(<FollowMark followed={false} />);

    expect(container).toBeEmptyDOMElement();
  });

  it("says a followed mission is followed", () => {
    render(<FollowMark followed />);

    expect(screen.getByLabelText("Projet suivi")).toBeInTheDocument();
    expect(screen.queryByRole("button")).not.toBeInTheDocument();
  });

  it("offers to follow a mission nobody follows", async () => {
    const onToggle = vi.fn();

    render(<FollowMark followed={false} onToggle={onToggle} />);
    const button = screen.getByRole("button", { name: "Suivre ce projet" });
    await userEvent.click(button);

    expect(button).toHaveAttribute("aria-pressed", "false");
    expect(onToggle).toHaveBeenCalledOnce();
  });

  it("offers to stop following a followed mission", async () => {
    const onToggle = vi.fn();

    render(<FollowMark followed onToggle={onToggle} />);
    const button = screen.getByRole("button", { name: "Ne plus suivre ce projet" });
    await userEvent.click(button);

    expect(button).toHaveAttribute("aria-pressed", "true");
    expect(onToggle).toHaveBeenCalledOnce();
  });

  /** La ligne entière ouvre déjà le projet : le clic ne doit pas y remonter. */
  it("keeps its click to itself", async () => {
    const rowClicked = vi.fn();

    render(
      <div onClick={rowClicked}>
        <FollowMark followed onToggle={vi.fn()} />
      </div>,
    );
    await userEvent.click(screen.getByRole("button"));

    expect(rowClicked).not.toHaveBeenCalled();
  });
});
