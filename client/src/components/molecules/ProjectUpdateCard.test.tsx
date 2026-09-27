import { describe, expect, it, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import { ProjectUpdateCard } from "./ProjectUpdateCard";
import type { ProjectUpdateResponse } from "@/lib/api/generated/model";

const NOW = new Date("2026-09-23T10:00:00Z");

function anUpdate(over: Partial<ProjectUpdateResponse> = {}): ProjectUpdateResponse {
  return {
    id: 1,
    author: { id: 7, display_name: "L. Chen", initials: "LC" },
    body: "Le cadrage est signé.",
    published_at: "2026-09-23T09:00:00Z",
    edited_at: null,
    is_deleted: false,
    is_mine: true,
    reactions: [],
    ...over,
  };
}

function renderCard(
  over: Partial<ProjectUpdateResponse> = {},
  onRemove = vi.fn(),
  aimed = false,
  onFlag = vi.fn(),
  editable = true,
) {
  render(
    <ProjectUpdateCard
      update={anUpdate(over)}
      now={NOW}
      aimed={aimed}
      onEdit={vi.fn()}
      onRemove={onRemove}
      onReact={vi.fn()}
      onFlag={onFlag}
      editable={editable}
    />,
  );
  return onRemove;
}

describe("ProjectUpdateCard", () => {
  it("marks out the update one was sent to, and brings it under the eye", () => {
    const scrolled = vi.spyOn(Element.prototype, "scrollIntoView");

    renderCard({}, vi.fn(), true);

    expect(screen.getByRole("article")).toHaveClass("aimed-at");
    expect(scrolled).toHaveBeenCalled();
    scrolled.mockRestore();
  });

  it("leaves every other update of the thread alone", () => {
    renderCard();

    expect(screen.getByRole("article")).not.toHaveClass("aimed-at");
  });

  it("asks before withdrawing, and withdraws nothing yet", async () => {
    const onRemove = renderCard();

    await userEvent.click(
      screen.getByRole("button", { name: "Supprimer la mise à jour" }),
    );

    expect(screen.getByRole("alertdialog")).toBeInTheDocument();
    expect(onRemove).not.toHaveBeenCalled();
  });

  it("withdraws the update once confirmed", async () => {
    const onRemove = renderCard();

    await userEvent.click(
      screen.getByRole("button", { name: "Supprimer la mise à jour" }),
    );
    await userEvent.click(screen.getByRole("button", { name: "Supprimer" }));

    expect(onRemove).toHaveBeenCalledTimes(1);
    expect(screen.queryByRole("alertdialog")).not.toBeInTheDocument();
  });

  it("withdraws nothing when one backs out of the dialog", async () => {
    const onRemove = renderCard();

    await userEvent.click(
      screen.getByRole("button", { name: "Supprimer la mise à jour" }),
    );
    await userEvent.click(screen.getByRole("button", { name: "Annuler" }));

    expect(onRemove).not.toHaveBeenCalled();
  });

  it("offers no withdrawal on somebody else's update", () => {
    // The thread is not a wiki: everyone answers for their own words.
    renderCard({ is_mine: false });

    expect(
      screen.queryByRole("button", { name: "Supprimer la mise à jour" }),
    ).not.toBeInTheDocument();
  });

  it("offers no withdrawal on an update already withdrawn", () => {
    renderCard({ is_deleted: true, body: "" });

    expect(
      screen.queryByRole("button", { name: "Supprimer la mise à jour" }),
    ).not.toBeInTheDocument();
    expect(screen.getByText("Message supprimé")).toBeInTheDocument();
  });

  describe("mise à l'ordre du jour de la revue", () => {
    it("offers to raise an update nobody has raised", async () => {
      const onFlag = vi.fn();
      renderCard({}, vi.fn(), false, onFlag);

      await userEvent.click(
        screen.getByRole("button", { name: /à discuter en revue/i }),
      );

      expect(onFlag).toHaveBeenCalledWith(true);
    });

    it("says who raised it, and offers to lower it", async () => {
      const onFlag = vi.fn();
      renderCard(
        { is_flagged: true, flagged_by: "N. Garo", flagged_at: "2026-09-23T09:30:00Z" },
        vi.fn(),
        false,
        onFlag,
      );

      expect(screen.getByText(/à discuter en revue/i)).toBeInTheDocument();
      expect(screen.getByText(/N. Garo/)).toBeInTheDocument();

      await userEvent.click(
        screen.getByRole("button", { name: /retirer de l'ordre du jour/i }),
      );

      expect(onFlag).toHaveBeenCalledWith(false);
    });

    it("offers the gesture to anybody, not only to the author", async () => {
      const onFlag = vi.fn();
      renderCard({ is_mine: false }, vi.fn(), false, onFlag);

      await userEvent.click(
        screen.getByRole("button", { name: /à discuter en revue/i }),
      );

      expect(onFlag).toHaveBeenCalledWith(true);
    });

    it("offers nothing to a reader who may not write", () => {
      renderCard({}, vi.fn(), false, vi.fn(), false);

      expect(
        screen.queryByRole("button", { name: /à discuter en revue/i }),
      ).not.toBeInTheDocument();
    });

    it("says nothing of a withdrawn update: there is nothing left to discuss", () => {
      renderCard({ is_deleted: true });

      expect(
        screen.queryByRole("button", { name: /à discuter en revue/i }),
      ).not.toBeInTheDocument();
    });
  });
});
