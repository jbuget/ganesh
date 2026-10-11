import { describe, expect, it, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import { TagMark } from "./TagMark";

const CHRONOPOST = { id: 1, name: "Chronopost", color: "violet" } as const;

describe("TagMark", () => {
  it("writes the tag in ordinary text", () => {
    render(<TagMark tag={CHRONOPOST} />);

    expect(screen.getByText("Chronopost")).toBeInTheDocument();
  });

  it("marks the tag with a diamond, distinct from a phase's dot and a square axis", () => {
    const { container } = render(<TagMark tag={CHRONOPOST} />);

    const diamond = container.querySelector("span span");
    expect(diamond?.getAttribute("class")).toContain("rotate-45");
  });

  it("paints the diamond in the colour of the tag", () => {
    const { container } = render(<TagMark tag={CHRONOPOST} />);

    const diamond = container.querySelector("span span");
    expect(diamond?.getAttribute("class")).toContain("bg-violet-500");
  });

  it("offers no way to take the tag off where it is only read", () => {
    render(<TagMark tag={CHRONOPOST} />);

    expect(screen.queryByRole("button")).not.toBeInTheDocument();
  });

  it("takes the tag off in one click when it may be changed", async () => {
    const onRemove = vi.fn();
    render(<TagMark tag={CHRONOPOST} onRemove={onRemove} />);

    await userEvent.click(
      screen.getByRole("button", { name: "Retirer le tag Chronopost" }),
    );

    expect(onRemove).toHaveBeenCalledOnce();
  });

  it("carries the pointer cursor on what is clickable", () => {
    render(<TagMark tag={CHRONOPOST} onRemove={() => {}} />);

    expect(screen.getByRole("button").className).toContain("cursor-pointer");
  });
});
