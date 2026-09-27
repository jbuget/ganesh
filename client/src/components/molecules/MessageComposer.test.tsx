import { describe, expect, it, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import { MessageComposer } from "./MessageComposer";

// ProseMirror holds its content outside React and does not type in jsdom.
vi.mock("@/components/atoms/RichTextEditor", () => ({
  RichTextEditor: ({
    placeholder,
    onChange,
    onSubmit,
  }: {
    placeholder?: string;
    onChange: (body: string) => void;
    onSubmit: () => void;
  }) => (
    <textarea
      aria-label={placeholder ?? "Éditeur"}
      onChange={(event) => onChange(event.target.value)}
      onKeyDown={(event) => {
        if (event.key === "Enter" && event.metaKey) onSubmit();
      }}
    />
  ),
}));

function renderComposer(over: Partial<Parameters<typeof MessageComposer>[0]> = {}) {
  const onConfirm = vi.fn().mockResolvedValue(undefined);
  const onCancel = vi.fn();
  render(
    <MessageComposer
      confirm="Répondre"
      onConfirm={onConfirm}
      onCancel={onCancel}
      {...over}
    />,
  );
  return { onConfirm, onCancel };
}

describe("MessageComposer", () => {
  it("names its own gesture, on the button and in the shortcut", () => {
    renderComposer({ confirm: "Enregistrer" });

    expect(screen.getByRole("button", { name: "Enregistrer" })).toBeInTheDocument();
    expect(screen.getByText("⌘↵ pour enregistrer")).toBeInTheDocument();
  });

  it("sends what was typed", async () => {
    const { onConfirm } = renderComposer();

    await userEvent.type(screen.getByLabelText("Éditeur"), "Fini hier soir.");
    await userEvent.click(screen.getByRole("button", { name: "Répondre" }));

    expect(onConfirm).toHaveBeenCalledWith("Fini hier soir.");
  });

  it("sends nothing while nothing is typed", async () => {
    const { onConfirm } = renderComposer();

    expect(screen.getByRole("button", { name: "Répondre" })).toBeDisabled();
    expect(onConfirm).not.toHaveBeenCalled();
  });

  it("sends nothing but blanks", async () => {
    const { onConfirm } = renderComposer();

    await userEvent.type(screen.getByLabelText("Éditeur"), "   ");

    expect(screen.getByRole("button", { name: "Répondre" })).toBeDisabled();
    expect(onConfirm).not.toHaveBeenCalled();
  });

  it("sends on ⌘↵ too", async () => {
    const { onConfirm } = renderComposer();

    const editor = screen.getByLabelText("Éditeur");
    await userEvent.type(editor, "Fini hier soir.");
    await userEvent.keyboard("{Meta>}{Enter}{/Meta}");

    expect(onConfirm).toHaveBeenCalledWith("Fini hier soir.");
  });

  it("opens on what is already written, when one is correcting", () => {
    renderComposer({ value: "Le cadrage est signé.", confirm: "Enregistrer" });

    expect(screen.getByRole("button", { name: "Enregistrer" })).toBeEnabled();
  });

  it("backs out without sending", async () => {
    const { onConfirm, onCancel } = renderComposer();

    await userEvent.type(screen.getByLabelText("Éditeur"), "Fini hier soir.");
    await userEvent.click(screen.getByRole("button", { name: "Annuler" }));

    expect(onCancel).toHaveBeenCalledTimes(1);
    expect(onConfirm).not.toHaveBeenCalled();
  });

  it("says what the editor is for", () => {
    renderComposer({ placeholder: "Répondez, et mentionnez quelqu'un avec @" });

    expect(
      screen.getByLabelText("Répondez, et mentionnez quelqu'un avec @"),
    ).toBeInTheDocument();
  });
});
