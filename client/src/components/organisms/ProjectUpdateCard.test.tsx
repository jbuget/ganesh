import { describe, expect, it, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import { ProjectUpdateCard } from "./ProjectUpdateCard";
import type {
  ProjectUpdateResponse,
  UpdateCommentResponse,
} from "@/lib/api/generated/model";

// ProseMirror holds its content outside React and does not type in jsdom.
// What this file is about is the card around it: which gestures it offers,
// and what it does with the text it is handed.
vi.mock("@/components/atoms/RichTextEditor", () => ({
  RichTextEditor: ({
    placeholder,
    onChange,
  }: {
    placeholder?: string;
    onChange: (body: string) => void;
  }) => (
    <textarea
      aria-label={placeholder ?? "Éditeur"}
      onChange={(event) => onChange(event.target.value)}
    />
  ),
}));

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

function aComment(over: Partial<UpdateCommentResponse> = {}): UpdateCommentResponse {
  return {
    id: 10,
    author: { id: 8, display_name: "N. Garo", initials: "NG" },
    body: "Fini hier soir.",
    published_at: "2026-09-23T09:30:00Z",
    edited_at: null,
    is_deleted: false,
    is_mine: false,
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
      onReply={vi.fn()}
      onEditComment={vi.fn()}
      onRemoveComment={vi.fn()}
      onReactToComment={vi.fn()}
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

  describe("la conversation sous une mise à jour", () => {
    function renderConversation(
      over: Partial<ProjectUpdateResponse> = {},
      handlers: Record<string, ReturnType<typeof vi.fn>> = {},
    ) {
      const all = {
        onReply: vi.fn(),
        onEditComment: vi.fn(),
        onRemoveComment: vi.fn(),
        onReactToComment: vi.fn(),
        ...handlers,
      };
      render(
        <ProjectUpdateCard
          update={anUpdate(over)}
          now={NOW}
          onEdit={vi.fn()}
          onRemove={vi.fn()}
          onReact={vi.fn()}
          onFlag={vi.fn()}
          {...all}
        />,
      );
      return all;
    }

    it("draws the replies in the order they were written", () => {
      renderConversation({
        comments: [
          aComment({ id: 10, body: "Fini hier soir." }),
          aComment({ id: 11, body: "Super." }),
        ],
      });

      const said = screen.getAllByRole("article").slice(1);
      expect(said).toHaveLength(2);
      expect(said[0]).toHaveTextContent("Fini hier soir.");
      expect(said[1]).toHaveTextContent("Super.");
    });

    it("opens a composer and answers with it", async () => {
      const { onReply } = renderConversation();

      await userEvent.click(screen.getByRole("button", { name: "Répondre" }));
      await userEvent.type(
        screen.getByLabelText("Répondez, et mentionnez quelqu'un avec @"),
        "Fini hier soir.",
      );
      await userEvent.click(
        screen.getAllByRole("button", { name: "Répondre" }).at(-1)!,
      );

      expect(onReply).toHaveBeenCalledWith("Fini hier soir.");
    });

    it("answers nothing while nothing is typed", async () => {
      const { onReply } = renderConversation();

      await userEvent.click(screen.getByRole("button", { name: "Répondre" }));

      expect(screen.getAllByRole("button", { name: "Répondre" }).at(-1)).toBeDisabled();
      expect(onReply).not.toHaveBeenCalled();
    });

    it("offers no answer on a withdrawn update", () => {
      // Refused by the domain too: there is nothing left to answer.
      renderConversation({ is_deleted: true, body: "" });

      expect(
        screen.queryByRole("button", { name: "Répondre" }),
      ).not.toBeInTheDocument();
    });

    it("keeps the replies of a withdrawn update", () => {
      renderConversation({
        is_deleted: true,
        body: "",
        comments: [aComment({ body: "Fini hier soir." })],
      });

      expect(screen.getByText("Fini hier soir.")).toBeInTheDocument();
    });

    it("offers no answer to a reader who may not write", () => {
      render(
        <ProjectUpdateCard
          update={anUpdate()}
          now={NOW}
          editable={false}
          onEdit={vi.fn()}
          onRemove={vi.fn()}
          onReact={vi.fn()}
          onFlag={vi.fn()}
          onReply={vi.fn()}
          onEditComment={vi.fn()}
          onRemoveComment={vi.fn()}
          onReactToComment={vi.fn()}
        />,
      );

      expect(
        screen.queryByRole("button", { name: "Répondre" }),
      ).not.toBeInTheDocument();
    });

    it("offers the withdrawal of a reply to its author alone", () => {
      renderConversation({ comments: [aComment({ is_mine: true })] });

      expect(
        screen.getByRole("button", { name: "Supprimer la réponse" }),
      ).toBeInTheDocument();
    });

    it("offers nothing on somebody else's reply", () => {
      renderConversation({ comments: [aComment({ is_mine: false })] });

      expect(
        screen.queryByRole("button", { name: "Supprimer la réponse" }),
      ).not.toBeInTheDocument();
    });

    it("withdraws a reply once confirmed", async () => {
      const { onRemoveComment } = renderConversation({
        comments: [aComment({ id: 42, is_mine: true })],
      });

      await userEvent.click(
        screen.getByRole("button", { name: "Supprimer la réponse" }),
      );
      await userEvent.click(screen.getByRole("button", { name: "Supprimer" }));

      expect(onRemoveComment).toHaveBeenCalledWith(42);
    });

    it("keeps a withdrawn reply in its place, without its words", () => {
      renderConversation({
        comments: [aComment({ is_deleted: true, body: "" })],
      });

      expect(screen.getByText("Message supprimé")).toBeInTheDocument();
    });
  });
});
