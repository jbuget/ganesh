import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/react";

import { UserAvatar } from "./UserAvatar";

describe("UserAvatar", () => {
  it("affiche les initiales", () => {
    render(<UserAvatar initials="JB" name="Jérémy Buget" />);

    expect(screen.getByText("JB")).toBeInTheDocument();
  });

  it("donne le nom complet, que des initiales ne laissent pas deviner", () => {
    render(<UserAvatar initials="JB" name="Jérémy Buget" />);

    expect(screen.getByTitle("Jérémy Buget")).toBeInTheDocument();
  });

  it("atténue la pastille d'un collaborateur inactif", () => {
    const { container } = render(<UserAvatar initials="LC" name="L. Chen" attenue />);

    expect(container.firstElementChild?.className).toContain("opacity-50");
  });
});
