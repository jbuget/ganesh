import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/react";

import { MemberAvatars } from "./MemberAvatars";
import type { BoardMemberResponse } from "@/lib/api/generated/model";

const membre = (id: number, nom: string, initiales: string): BoardMemberResponse =>
  ({ id, display_name: nom, initiales }) as BoardMemberResponse;

describe("MemberAvatars", () => {
  it("affiche les initiales de chaque intervenant", () => {
    render(
      <MemberAvatars
        membres={[membre(1, "Léa Chen", "LC"), membre(2, "David Dehe", "DD")]}
      />,
    );

    expect(screen.getByText("LC")).toBeInTheDocument();
    expect(screen.getByText("DD")).toBeInTheDocument();
  });

  it("donne le nom complet au survol", () => {
    render(<MemberAvatars membres={[membre(1, "Léa Chen", "LC")]} />);

    expect(screen.getByText("LC")).toHaveAttribute("title", "Léa Chen");
  });

  it("n'affiche rien quand personne n'a encore saisi", () => {
    const { container } = render(<MemberAvatars membres={[]} />);

    expect(container).toBeEmptyDOMElement();
  });

  it("résume les intervenants au-delà de quatre", () => {
    const membres = Array.from({ length: 7 }, (_, i) =>
      membre(i, `Personne ${i}`, `P${i}`),
    );
    render(<MemberAvatars membres={membres} />);

    expect(screen.getByText("+3")).toBeInTheDocument();
  });

  it("nomme dans l'infobulle ceux qui sont résumés", () => {
    const membres = Array.from({ length: 6 }, (_, i) =>
      membre(i, `Personne ${i}`, `P${i}`),
    );
    render(<MemberAvatars membres={membres} />);

    expect(screen.getByText("+2")).toHaveAttribute("title", "Personne 4, Personne 5");
  });
});
