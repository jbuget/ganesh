import { describe, expect, it } from "vitest";
import { fireEvent, render, screen } from "@testing-library/react";

import { MemberAvatars } from "./MemberAvatars";
import type { BoardMemberResponse } from "@/lib/api/generated/model";

const member = (id: number, name: string, initials: string): BoardMemberResponse =>
  ({ id, display_name: name, initials }) as BoardMemberResponse;

describe("MemberAvatars", () => {
  it("affiche les initiales de chaque intervenant", () => {
    render(
      <MemberAvatars
        members={[member(1, "Léa Chen", "LC"), member(2, "David Dehe", "DD")]}
      />,
    );

    expect(screen.getByText("LC")).toBeInTheDocument();
    expect(screen.getByText("DD")).toBeInTheDocument();
  });

  it("donne le nom complet au survol, sans attendre", () => {
    render(<MemberAvatars members={[member(1, "Léa Chen", "LC")]} />);

    fireEvent.mouseMove(screen.getByText("LC"), { clientX: 10, clientY: 10 });

    expect(screen.getByRole("tooltip")).toHaveTextContent("Léa Chen");
  });

  it("retire l'infobulle quand la souris quitte les pastilles", () => {
    render(<MemberAvatars members={[member(1, "Léa Chen", "LC")]} />);
    const dot = screen.getByText("LC");

    fireEvent.mouseMove(dot, { clientX: 10, clientY: 10 });
    fireEvent.mouseLeave(dot.parentElement!);

    expect(screen.queryByRole("tooltip")).toBeNull();
  });

  it("n'affiche rien quand personne n'a encore saisi", () => {
    const { container } = render(<MemberAvatars members={[]} />);

    expect(container).toBeEmptyDOMElement();
  });

  it("résume les intervenants au-delà de quatre", () => {
    const members = Array.from({ length: 7 }, (_, i) =>
      member(i, `Personne ${i}`, `P${i}`),
    );
    render(<MemberAvatars members={members} />);

    expect(screen.getByText("+3")).toBeInTheDocument();
  });

  it("nomme dans l'infobulle ceux qui sont résumés", () => {
    const members = Array.from({ length: 6 }, (_, i) =>
      member(i, `Personne ${i}`, `P${i}`),
    );
    render(<MemberAvatars members={members} />);

    fireEvent.mouseMove(screen.getByText("+2"), { clientX: 10, clientY: 10 });

    expect(screen.getByRole("tooltip")).toHaveTextContent("Personne 4, Personne 5");
  });
});
