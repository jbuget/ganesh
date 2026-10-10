import { describe, expect, it, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import { AssistantComposer } from "./AssistantComposer";

function field() {
  return screen.getByRole("textbox", { name: "Votre question" });
}

describe("AssistantComposer", () => {
  it("asks the question on Entrée, and empties the field", async () => {
    const onAsk = vi.fn();
    render(<AssistantComposer placeholder="…" onAsk={onAsk} />);

    await userEvent.type(field(), "Où en est WAATcher ?{Enter}");

    expect(onAsk).toHaveBeenCalledWith("Où en est WAATcher ?");
    expect(field()).toHaveValue("");
  });

  it("goes to the line on Maj+Entrée rather than asking", async () => {
    const onAsk = vi.fn();
    render(<AssistantComposer placeholder="…" onAsk={onAsk} />);

    await userEvent.type(field(), "Où en est{Shift>}{Enter}{/Shift}WAATcher ?");

    expect(onAsk).not.toHaveBeenCalled();
    expect(field()).toHaveValue("Où en est\nWAATcher ?");
  });

  it("asks the question from the button", async () => {
    const onAsk = vi.fn();
    render(<AssistantComposer placeholder="…" onAsk={onAsk} />);

    await userEvent.type(field(), "Où en est WAATcher ?");
    await userEvent.click(screen.getByRole("button", { name: "Envoyer" }));

    expect(onAsk).toHaveBeenCalledWith("Où en est WAATcher ?");
  });

  it("asks nothing of a blank question", async () => {
    const onAsk = vi.fn();
    render(<AssistantComposer placeholder="…" onAsk={onAsk} />);

    await userEvent.type(field(), "   {Enter}");

    expect(onAsk).not.toHaveBeenCalled();
  });

  it("asks nothing while it is held back", async () => {
    const onAsk = vi.fn();
    render(<AssistantComposer placeholder="…" disabled onAsk={onAsk} />);

    expect(field()).toBeDisabled();
    expect(screen.getByRole("button", { name: "Envoyer" })).toBeDisabled();
  });
});
