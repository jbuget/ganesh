import { describe, expect, it, vi } from "vitest";
import { render, screen } from "@testing-library/react";

import { UnansweredQuestionPanel } from "./UnansweredQuestionPanel";

describe("UnansweredQuestionPanel", () => {
  it("says why the question went unanswered and what was read before", () => {
    render(
      <UnansweredQuestionPanel
        question={{
          id: 1,
          conversation_id: "c0nv",
          asker_id: 4,
          project_id: 7,
          asked_at: "2026-10-10T14:49:25Z",
          question: "Qui fait quoi en ce moment ?",
          reason: "kept_asking",
          consultations: [
            {
              tool: "find_project",
              arguments: { query: "tout" },
              result: "Douze projets.",
            },
          ],
          model: "gemini-3.8-flash",
          input_tokens: 9000,
          output_tokens: 0,
          elapsed_ms: 14000,
        }}
        askerName="Damien"
        projectLabel={() => "WAATcher"}
        onClose={vi.fn()}
      />,
    );

    expect(screen.getByText("Qui fait quoi en ce moment ?")).toBeInTheDocument();
    expect(screen.getByText("Lectures sans fin")).toBeInTheDocument();
    expect(screen.getByText(/depuis la fiche WAATcher/)).toBeInTheDocument();
    expect(screen.getByText("find_project")).toBeInTheDocument();
    expect(screen.getByText("Douze projets.")).toBeInTheDocument();
  });
});
