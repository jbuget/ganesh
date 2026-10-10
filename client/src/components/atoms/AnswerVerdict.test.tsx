import { describe, expect, it, vi } from "vitest";
import { fireEvent, render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import { AnswerVerdict } from "./AnswerVerdict";

describe("AnswerVerdict", () => {
  it("says an answer helped", async () => {
    const onJudge = vi.fn();
    render(<AnswerVerdict verdict={null} onJudge={onJudge} />);

    await userEvent.click(screen.getByRole("button", { name: "Réponse utile" }));

    expect(onJudge).toHaveBeenCalledWith("helpful");
  });

  it("says an answer did not help", async () => {
    const onJudge = vi.fn();
    render(<AnswerVerdict verdict={null} onJudge={onJudge} />);

    await userEvent.click(screen.getByRole("button", { name: "Réponse pas utile" }));

    expect(onJudge).toHaveBeenCalledWith("unhelpful");
  });

  it("shows the verdict already given", () => {
    render(<AnswerVerdict verdict="unhelpful" onJudge={vi.fn()} />);

    expect(screen.getByRole("button", { name: "Réponse pas utile" })).toHaveAttribute(
      "aria-pressed",
      "true",
    );
    expect(screen.getByRole("button", { name: "Réponse utile" })).toHaveAttribute(
      "aria-pressed",
      "false",
    );
  });

  it("colours a helpful answer green", () => {
    render(<AnswerVerdict verdict="helpful" onJudge={vi.fn()} />);

    expect(screen.getByRole("button", { name: "Réponse utile" })).toHaveClass(
      "text-emerald-600",
    );
  });

  it("colours an unhelpful answer red", () => {
    render(<AnswerVerdict verdict="unhelpful" onJudge={vi.fn()} />);

    expect(screen.getByRole("button", { name: "Réponse pas utile" })).toHaveClass(
      "text-red-600",
    );
  });

  it("springs the thumb clicked, and only that one", async () => {
    render(<AnswerVerdict verdict={null} onJudge={vi.fn()} />);

    await userEvent.click(screen.getByRole("button", { name: "Réponse utile" }));

    expect(screen.getByRole("button", { name: "Réponse utile" })).toHaveClass(
      "verdict-up",
    );
    expect(screen.getByRole("button", { name: "Réponse pas utile" })).not.toHaveClass(
      "verdict-down",
    );
  });

  it("does not spring a verdict it was handed rather than given", () => {
    render(<AnswerVerdict verdict="helpful" onJudge={vi.fn()} />);

    expect(screen.getByRole("button", { name: "Réponse utile" })).not.toHaveClass(
      "verdict-up",
    );
  });

  it("lets the spring go once it has played", async () => {
    render(<AnswerVerdict verdict={null} onJudge={vi.fn()} />);
    const thumb = screen.getByRole("button", { name: "Réponse pas utile" });

    await userEvent.click(thumb);
    // jsdom knows no CSS animation, so React listens for the prefixed name.
    fireEvent(thumb, new Event("webkitAnimationEnd", { bubbles: true }));

    expect(thumb).not.toHaveClass("verdict-down");
  });
});
