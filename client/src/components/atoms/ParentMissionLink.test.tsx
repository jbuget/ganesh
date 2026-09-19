import { describe, expect, it, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import { ParentMissionLink } from "./ParentMissionLink";

const PARENT = { id: 7, label: "Espace locataire" };

describe("ParentMissionLink", () => {
  it("says the mission is a work package, and of which project", () => {
    render(<ParentMissionLink parent={PARENT} onOpen={vi.fn()} />);

    const link = screen.getByRole("button");
    expect(link).toHaveTextContent("Sous-projet");
    expect(link).toHaveTextContent("Espace locataire");
  });

  /**
   * Beside the board, one stays beside the board: the panel swaps missions
   * rather than taking the reader off the screen they were working on.
   */
  it("opens the project it belongs to, in place", async () => {
    const onOpen = vi.fn();
    render(<ParentMissionLink parent={PARENT} onOpen={onOpen} />);

    await userEvent.click(screen.getByRole("button"));

    expect(onOpen).toHaveBeenCalledWith(7);
  });

  /** On a full page there is no panel to swap: one navigates. */
  it("leads to the project's own page when there is no panel to swap", () => {
    render(<ParentMissionLink parent={PARENT} />);

    expect(screen.getByRole("link")).toHaveAttribute("href", "/projects/7");
  });
});
