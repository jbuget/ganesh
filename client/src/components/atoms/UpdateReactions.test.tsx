import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { UpdateReactions } from "@/components/atoms/UpdateReactions";
import { Reaction, type UpdateReactionResponse } from "@/lib/api/generated/model";

const thumbs: UpdateReactionResponse = {
  reaction: Reaction.thumbs_up,
  people: ["L. Chen", "N. Garo"],
  is_mine: false,
};

function draw(reactions: UpdateReactionResponse[] = [], onToggle = vi.fn()) {
  render(<UpdateReactions reactions={reactions} onToggle={onToggle} />);
  return onToggle;
}

describe("the signs under an update", () => {
  it("shows each sign with how many left it", () => {
    draw([thumbs]);

    expect(screen.getByRole("button", { name: /D'accord/ })).toHaveTextContent("2");
  });

  it("names on hover who left it", () => {
    draw([thumbs]);

    fireEvent.mouseMove(screen.getByRole("button", { name: /D'accord/ }));

    expect(screen.getByRole("tooltip")).toHaveTextContent(
      "D'accord : L. Chen et N. Garo",
    );
  });

  it("lets go of the tooltip on leaving", () => {
    draw([thumbs]);
    const chip = screen.getByRole("button", { name: /D'accord/ });
    fireEvent.mouseMove(chip);

    fireEvent.mouseLeave(chip);

    expect(screen.queryByRole("tooltip")).not.toBeInTheDocument();
  });

  it("leaves the native tooltip alone: it comes a second too late", () => {
    draw([thumbs]);

    expect(screen.getByRole("button", { name: /D'accord/ })).not.toHaveAttribute(
      "title",
    );
  });

  it("names each sign of the set on hover", () => {
    draw([]);
    fireEvent.click(screen.getByRole("button", { name: "Réagir" }));

    fireEvent.mouseMove(screen.getByRole("button", { name: "Bravo" }));

    expect(screen.getByRole("tooltip")).toHaveTextContent("Bravo");
  });

  it("marks the sign the reader left", () => {
    draw([{ ...thumbs, is_mine: true }]);

    expect(screen.getByRole("button", { name: /D'accord/ })).toHaveAttribute(
      "aria-pressed",
      "true",
    );
  });

  it("leaves a sign on click", () => {
    const onToggle = draw([thumbs]);

    fireEvent.click(screen.getByRole("button", { name: /D'accord/ }));

    expect(onToggle).toHaveBeenCalledWith(Reaction.thumbs_up, true);
  });

  it("takes back the reader's own sign on click", () => {
    const onToggle = draw([{ ...thumbs, is_mine: true }]);

    fireEvent.click(screen.getByRole("button", { name: /D'accord/ }));

    expect(onToggle).toHaveBeenCalledWith(Reaction.thumbs_up, false);
  });

  it("offers the whole set behind one button", () => {
    draw([]);

    fireEvent.click(screen.getByRole("button", { name: "Réagir" }));

    expect(screen.getByRole("button", { name: "Bravo" })).toBeInTheDocument();
  });

  it("leaves the sign picked from the set", () => {
    const onToggle = draw([]);
    fireEvent.click(screen.getByRole("button", { name: "Réagir" }));

    fireEvent.click(screen.getByRole("button", { name: "Bravo" }));

    expect(onToggle).toHaveBeenCalledWith(Reaction.hooray, true);
  });

  it("takes a sign back when the reader picks one they already left", () => {
    /* The reader's own signs, not the thread's: someone else's thumbs-up is
       not mine to take back. */
    const onToggle = draw([
      thumbs,
      { ...thumbs, reaction: Reaction.hooray, is_mine: true },
    ]);
    fireEvent.click(screen.getByRole("button", { name: "Réagir" }));

    fireEvent.click(screen.getByRole("button", { name: "Bravo" }));

    expect(onToggle).toHaveBeenCalledWith(Reaction.hooray, false);
  });

  it("a sign somebody else left is still mine to leave", () => {
    const onToggle = draw([thumbs]);
    fireEvent.click(screen.getByRole("button", { name: "Réagir" }));

    fireEvent.click(screen.getByRole("button", { name: "D'accord" }));

    expect(onToggle).toHaveBeenCalledWith(Reaction.thumbs_up, true);
  });
});
