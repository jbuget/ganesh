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

function renderCard(over: Partial<ProjectUpdateResponse> = {}, onRemove = vi.fn()) {
  render(
    <ProjectUpdateCard
      update={anUpdate(over)}
      now={NOW}
      onEdit={vi.fn()}
      onRemove={onRemove}
      onReact={vi.fn()}
    />,
  );
  return onRemove;
}

describe("ProjectUpdateCard", () => {
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
});
