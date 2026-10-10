import { beforeEach, describe, expect, it, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import type { Assistant } from "@/lib/use-assistant";

import { AssistantPanel } from "./AssistantPanel";

const assistant = vi.hoisted(() => ({ current: {} as Assistant }));

vi.mock("@/lib/use-assistant", () => ({ useAssistant: () => assistant.current }));
vi.mock("@/lib/assistant-store", () => ({ useAssistantShortcut: () => {} }));

function opened(fields: Partial<Assistant> = {}): Assistant {
  return {
    isOpen: true,
    close: vi.fn(),
    isAvailable: true,
    projectId: null,
    turns: [],
    pending: null,
    remaining: 5,
    names: new Map(),
    maxExchanges: 5,
    isOver: false,
    refusal: null,
    ask: vi.fn(),
    judge: vi.fn(),
    restart: vi.fn(),
    ...fields,
  };
}

beforeEach(() => {
  assistant.current = opened();
});

describe("AssistantPanel", () => {
  it("draws nothing while it is put away", () => {
    assistant.current = opened({ isOpen: false });

    const { container } = render(<AssistantPanel />);

    expect(container).toBeEmptyDOMElement();
  });

  it("says what it can be asked before anybody asks", () => {
    render(<AssistantPanel />);

    expect(
      screen.getByRole("complementary", { name: "Assistant" }),
    ).toBeInTheDocument();
    expect(screen.getByText(/où en est un projet/)).toBeInTheDocument();
  });

  it("says the exchanges are kept", () => {
    render(<AssistantPanel />);

    expect(screen.getByText(/sont conservées pour améliorer/)).toBeInTheDocument();
  });

  it("says why a conversation stops at a few questions", () => {
    render(<AssistantPanel />);

    expect(
      screen.getByText(
        "Pour limiter les erreurs et garder des réponses pertinentes, une " +
          "conversation compte 5 questions au plus.",
      ),
    ).toBeInTheDocument();
  });

  it("asks the question typed", async () => {
    const ask = vi.fn();
    assistant.current = opened({ ask });
    render(<AssistantPanel />);

    await userEvent.type(screen.getByRole("textbox"), "Où en est WAATcher ?{Enter}");

    expect(ask).toHaveBeenCalledWith("Où en est WAATcher ?");
  });

  it("offers to ask about the project in view", () => {
    assistant.current = opened({ projectId: 7 });
    render(<AssistantPanel />);

    expect(screen.getByRole("textbox")).toHaveAttribute(
      "placeholder",
      "Une question sur ce projet…",
    );
  });

  it("shows the question on its way while the answer is awaited", () => {
    assistant.current = opened({ pending: "Où en est WAATcher ?" });
    render(<AssistantPanel />);

    expect(screen.getByText("Où en est WAATcher ?")).toBeInTheDocument();
    expect(screen.getByText("Ganesh cherche…")).toBeInTheDocument();
    expect(screen.getByRole("textbox")).toBeDisabled();
  });

  it("says why a question went unanswered", () => {
    assistant.current = opened({ refusal: "L'assistant n'a pas pu répondre." });
    render(<AssistantPanel />);

    expect(screen.getByRole("alert")).toHaveTextContent(
      "L'assistant n'a pas pu répondre.",
    );
  });

  it("counts the questions the conversation still holds", () => {
    assistant.current = opened({
      remaining: 1,
      turns: [{ id: 1, question: "Q ?", answer: "R.", consulted: [], verdict: null }],
    });
    render(<AssistantPanel />);

    expect(screen.getByText("1 question restante")).toBeInTheDocument();
  });

  it("closes the field once the conversation is over, and offers a fresh one", async () => {
    const restart = vi.fn();
    assistant.current = opened({
      remaining: 0,
      isOver: true,
      restart,
      turns: [{ id: 5, question: "Q ?", answer: "R.", consulted: [], verdict: null }],
    });
    render(<AssistantPanel />);

    expect(screen.getByRole("textbox")).toBeDisabled();
    expect(screen.getByText(/Cette conversation est terminée/)).toBeInTheDocument();
    await userEvent.click(
      screen.getByRole("button", { name: "Nouvelle conversation" }),
    );
    expect(restart).toHaveBeenCalled();
  });

  it("says it does not answer when no model is configured", () => {
    assistant.current = opened({ isAvailable: false });
    render(<AssistantPanel />);

    expect(screen.getByText(/n'est pas configuré/)).toBeInTheDocument();
    expect(screen.queryByRole("textbox")).not.toBeInTheDocument();
  });

  it("closes", async () => {
    const close = vi.fn();
    assistant.current = opened({ close });
    render(<AssistantPanel />);

    await userEvent.click(screen.getByRole("button", { name: "Fermer" }));

    expect(close).toHaveBeenCalled();
  });
});
