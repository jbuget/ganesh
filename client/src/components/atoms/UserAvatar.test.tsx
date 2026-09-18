import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/react";

import { UserAvatar } from "./UserAvatar";

describe("UserAvatar", () => {
  it("shows the initials", () => {
    render(<UserAvatar initials="JB" name="Jérémy Buget" />);

    expect(screen.getByText("JB")).toBeInTheDocument();
  });

  it("gives the full name, which initials do not let one guess", () => {
    render(<UserAvatar initials="JB" name="Jérémy Buget" />);

    expect(screen.getByTitle("Jérémy Buget")).toBeInTheDocument();
  });

  it("dims the avatar of an inactive teammate", () => {
    const { container } = render(<UserAvatar initials="LC" name="L. Chen" attenue />);

    expect(container.firstElementChild?.className).toContain("opacity-50");
  });
});
