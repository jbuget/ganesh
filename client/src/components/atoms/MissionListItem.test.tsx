import { describe, expect, it, vi } from "vitest";
import { fireEvent, render, screen } from "@testing-library/react";

import { MissionListItem } from "./MissionListItem";

describe("MissionListItem", () => {
  it("affiche le nom de la mission", () => {
    render(<MissionListItem label="Portail bailleurs" onOpen={vi.fn()} />);

    expect(screen.getByRole("button")).toHaveTextContent("Portail bailleurs");
  });

  it("ouvre la mission au clic", () => {
    const onOpen = vi.fn();
    render(<MissionListItem label="Portail bailleurs" onOpen={onOpen} />);

    fireEvent.click(screen.getByRole("button"));

    expect(onOpen).toHaveBeenCalledTimes(1);
  });

  it("décale un lot sous son projet", () => {
    const { container } = render(
      <MissionListItem label="Lot 1 - API" estLot onOpen={vi.fn()} />,
    );

    expect(container.querySelector("button")?.className).toContain("pl-9");
  });

  it("ne porte aucune action en dehors de l'ouverture", () => {
    // Tout ce qui se modifie sur une mission se fait dans son panneau.
    render(<MissionListItem label="Portail bailleurs" onOpen={vi.fn()} />);

    expect(screen.getAllByRole("button")).toHaveLength(1);
  });
});
