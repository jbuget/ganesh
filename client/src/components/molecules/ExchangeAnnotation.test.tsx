import { describe, expect, it, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import { ExchangeAnnotation } from "./ExchangeAnnotation";

describe("ExchangeAnnotation", () => {
  it("asks for a cause before anything is saved", () => {
    render(
      <ExchangeAnnotation
        exchangeId={1}
        annotation={null}
        annotatorName={null}
        onAnnotate={vi.fn()}
      />,
    );

    expect(screen.getByRole("button", { name: "Enregistrer" })).toBeDisabled();
    expect(screen.getByText("Pas encore annotée.")).toBeInTheDocument();
  });

  it("saves the cause and the note given", async () => {
    const onAnnotate = vi.fn().mockResolvedValue(undefined);
    render(
      <ExchangeAnnotation
        exchangeId={1}
        annotation={null}
        annotatorName={null}
        onAnnotate={onAnnotate}
      />,
    );

    await userEvent.click(screen.getByRole("radio", { name: "Lecture fausse" }));
    await userEvent.type(
      screen.getByRole("textbox", { name: "Note" }),
      "Les lots manquent.",
    );
    await userEvent.click(screen.getByRole("button", { name: "Enregistrer" }));

    expect(onAnnotate).toHaveBeenCalledWith("wrong_reading", "Les lots manquent.");
  });

  it("says who read the answer, and offers nothing to save until it changes", () => {
    render(
      <ExchangeAnnotation
        exchangeId={1}
        annotation={{
          cause: "right_answer",
          note: null,
          annotated_by: 9,
          annotated_at: "2026-10-12T12:00:00Z",
        }}
        annotatorName="A. Admin"
        onAnnotate={vi.fn()}
      />,
    );

    expect(screen.getByRole("radio", { name: "Bonne réponse" })).toBeChecked();
    expect(
      screen.getByText(/Annotée par A\. Admin le 12\/10\/2026/),
    ).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Enregistrer" })).toBeDisabled();
  });
});
