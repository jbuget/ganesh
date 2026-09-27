import { describe, expect, it, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import { UpdateCommentCard } from "./UpdateCommentCard";
import type { UpdateCommentResponse } from "@/lib/api/generated/model";

// ProseMirror holds its content outside React and does not type in jsdom.
vi.mock("@/components/atoms/RichTextEditor", () => ({
  RichTextEditor: ({ onChange }: { onChange: (body: string) => void }) => (
    <textarea aria-label="Éditeur" onChange={(event) => onChange(event.target.value)} />
  ),
}));

const NOW = new Date("2026-09-27T12:00:00Z");

function aComment(over: Partial<UpdateCommentResponse> = {}): UpdateCommentResponse {
  return {
    id: 10,
    author: { id: 8, display_name: "N. Garo", initials: "NG" },
    body: "Fini hier soir.",
    published_at: "2026-09-27T11:00:00Z",
    edited_at: null,
    is_deleted: false,
    is_mine: true,
    reactions: [],
    ...over,
  };
}

function renderComment(
  over: Partial<UpdateCommentResponse> = {},
  handlers: Record<string, ReturnType<typeof vi.fn>> = {},
) {
  const all = {
    onEdit: vi.fn(),
    onRemove: vi.fn(),
    onReact: vi.fn(),
    ...handlers,
  };
  render(<UpdateCommentCard comment={aComment(over)} now={NOW} {...all} />);
  return all;
}

describe("UpdateCommentCard", () => {
  it("signs the reply and says when it was written", () => {
    renderComment();

    expect(screen.getByText("N. Garo")).toBeInTheDocument();
    expect(screen.getByText("NG")).toBeInTheDocument();
    expect(screen.getByText("Fini hier soir.")).toBeInTheDocument();
  });

  it("says a reply was corrected", () => {
    renderComment({ edited_at: "2026-09-27T11:30:00Z" });

    expect(screen.getByText(/modifiée/)).toBeInTheDocument();
  });

  it("carries no flag: one puts a subject on the agenda, not an answer", () => {
    renderComment();

    expect(
      screen.queryByRole("button", { name: /à discuter en revue/i }),
    ).not.toBeInTheDocument();
  });

  it("corrects the reply in place", async () => {
    const { onEdit } = renderComment();

    await userEvent.click(screen.getByRole("button", { name: "Modifier la réponse" }));
    await userEvent.type(screen.getByLabelText("Éditeur"), "Fini ce matin.");
    await userEvent.click(screen.getByRole("button", { name: "Enregistrer" }));

    expect(onEdit).toHaveBeenCalledWith("Fini ce matin.");
  });

  it("asks before withdrawing, and withdraws nothing yet", async () => {
    const { onRemove } = renderComment();

    await userEvent.click(screen.getByRole("button", { name: "Supprimer la réponse" }));

    expect(screen.getByRole("alertdialog")).toHaveTextContent(
      "Supprimer cette réponse ?",
    );
    expect(onRemove).not.toHaveBeenCalled();
  });

  it("offers nothing on somebody else's reply", () => {
    renderComment({ is_mine: false });

    expect(
      screen.queryByRole("button", { name: "Modifier la réponse" }),
    ).not.toBeInTheDocument();
    expect(
      screen.queryByRole("button", { name: "Supprimer la réponse" }),
    ).not.toBeInTheDocument();
  });

  it("keeps a withdrawn reply in place, without its words", () => {
    renderComment({ is_deleted: true, body: "" });

    expect(screen.getByText("Message supprimé")).toBeInTheDocument();
    expect(
      screen.queryByRole("button", { name: "Supprimer la réponse" }),
    ).not.toBeInTheDocument();
  });

  it("leaves a sign under the reply", async () => {
    const { onReact } = renderComment({
      reactions: [{ reaction: "thumbs_up", people: ["L. Chen"], is_mine: false }],
    });

    await userEvent.click(screen.getByRole("button", { name: /D'accord : L. Chen/ }));

    expect(onReact).toHaveBeenCalledWith("thumbs_up", true);
  });

  it("shows the signs already left to a reader who may not write", () => {
    // Who answered « lu » is part of the conversation, and a guest reads it.
    render(
      <UpdateCommentCard
        comment={aComment({
          reactions: [{ reaction: "heart", people: ["L. Chen"], is_mine: false }],
        })}
        now={NOW}
        editable={false}
        onEdit={vi.fn()}
        onRemove={vi.fn()}
        onReact={vi.fn()}
      />,
    );

    expect(screen.getByRole("button", { name: /J'aime : L. Chen/ })).toBeDisabled();
    expect(screen.queryByRole("button", { name: "Réagir" })).not.toBeInTheDocument();
  });
});
