import { describe, expect, it, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import { CommandPaletteRow } from "./CommandPaletteRow";
import type { Destination } from "@/lib/command-palette";

const NOW = new Date("2026-09-21T12:00:00Z");

const row = (over: Partial<Destination> = {}) =>
  ({
    key: "project:12",
    label: "Portail bailleurs",
    href: "/projects/12",
    group: "project",
    ...over,
  }) as Destination;

function draw(destination: Destination, selected = false) {
  return render(
    <ul>
      <CommandPaletteRow
        destination={destination}
        selected={selected}
        now={NOW}
        onOpen={vi.fn()}
        onHover={vi.fn()}
      />
    </ul>,
  );
}

describe("CommandPaletteRow", () => {
  it("names the destination", () => {
    draw(row());

    expect(
      screen.getByRole("option", { name: /Portail bailleurs/ }),
    ).toBeInTheDocument();
  });

  it("says what moved it and when, in that order", () => {
    draw(row({ gesture: "Phase changée", at: "2026-09-20T12:00:00Z" }));

    expect(screen.getByRole("option")).toHaveTextContent("Phase changée · hier");
  });

  it("adds what it belongs to after the rest", () => {
    draw(
      row({
        gesture: "Modifié",
        at: "2026-09-21T11:00:00Z",
        hint: "Sous-projet de RAGGAE",
      }),
    );

    expect(screen.getByRole("option")).toHaveTextContent(
      "Modifié · il y a 1 h · Sous-projet de RAGGAE",
    );
  });

  it("marks a project with the colour of its phase", () => {
    const { container } = draw(row({ status: "development" }));

    expect(container.querySelector("[title='Réalisation']")).toBeInTheDocument();
  });

  it("says nothing extra of a destination that carries nothing", () => {
    draw(row());

    expect(screen.getByRole("option")).toHaveTextContent("Portail bailleurs");
    expect(screen.getByRole("option").textContent).toBe("Portail bailleurs");
  });

  it("tells the palette it was chosen", async () => {
    const onOpen = vi.fn();
    const who = userEvent.setup();
    render(
      <ul>
        <CommandPaletteRow
          destination={row()}
          selected={false}
          now={NOW}
          onOpen={onOpen}
          onHover={vi.fn()}
        />
      </ul>,
    );

    await who.click(screen.getByRole("option"));

    expect(onOpen).toHaveBeenCalledOnce();
  });

  it("shows the selection where it stands", () => {
    draw(row(), true);

    expect(screen.getByRole("option")).toHaveAttribute("aria-selected", "true");
  });
});
