import { describe, expect, it, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import { AssistantExchange } from "./AssistantExchange";

const NAMES = new Map([
  ["EDIT", "/projects/85"],
  ["David DEHE", "/users?user=3"],
]);

const TURN = {
  id: 3,
  question: "Où en est WAATcher ?",
  answer: "WAATcher est **en développement**.",
  consulted: [{ id: 7, label: "WAATcher" }],
  verdict: null,
};

describe("AssistantExchange", () => {
  it("shows the question and the answer", () => {
    render(<AssistantExchange turn={TURN} names={NAMES} onJudge={vi.fn()} />);

    expect(screen.getByText("Où en est WAATcher ?")).toBeInTheDocument();
    expect(screen.getByText("en développement")).toBeInTheDocument();
  });

  it("leads to the projects the answer was read from", () => {
    render(<AssistantExchange turn={TURN} names={NAMES} onJudge={vi.fn()} />);

    expect(screen.getByText(/Lu dans/)).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "WAATcher" })).toHaveAttribute(
      "href",
      "/projects/7",
    );
  });

  it("says nothing of sources when no project was read", () => {
    render(
      <AssistantExchange
        turn={{ ...TURN, consulted: [] }}
        names={NAMES}
        onJudge={vi.fn()}
      />,
    );

    expect(screen.queryByText(/Lu dans/)).not.toBeInTheDocument();
  });

  it("judges this answer and no other", async () => {
    const onJudge = vi.fn();
    render(<AssistantExchange turn={TURN} names={NAMES} onJudge={onJudge} />);

    await userEvent.click(screen.getByRole("button", { name: "Réponse utile" }));

    expect(onJudge).toHaveBeenCalledWith(3, "helpful");
  });

  it("draws the projects and the people the answer names apart from its prose", () => {
    render(
      <AssistantExchange
        turn={{
          ...TURN,
          answer: "EDIT est porté par David DEHE.",
          consulted: [],
        }}
        names={NAMES}
        onJudge={vi.fn()}
      />,
    );

    expect(screen.getByRole("link", { name: "EDIT" })).toHaveClass("text-sky-700");
    expect(screen.getByRole("link", { name: "David DEHE" })).toHaveClass(
      "font-semibold",
    );
  });

  it("draws no image a model wrote, whatever it points at", () => {
    const { container } = render(
      <AssistantExchange
        turn={{ ...TURN, answer: "![x](https://ailleurs.example/?q=secret)" }}
        names={NAMES}
        onJudge={vi.fn()}
      />,
    );

    expect(container.querySelector("img")).toBeNull();
  });
});
