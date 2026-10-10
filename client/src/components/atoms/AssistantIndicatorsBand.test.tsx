import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/react";

import type { AssistantIndicatorsResponse } from "@/lib/api/generated/model";

import { AssistantIndicatorsBand } from "./AssistantIndicatorsBand";

const NOBODY_ASKED: AssistantIndicatorsResponse = {
  kept_since: null,
  questions: 0,
  conversations: 0,
  askers: 0,
  helpful: 0,
  unhelpful: 0,
  unjudged: 0,
  causes: [
    { cause: "wrong_reading", count: 0 },
    { cause: "wrong_phrasing", count: 0 },
    { cause: "out_of_scope", count: 0 },
    { cause: "right_answer", count: 0 },
  ],
  unannotated: 0,
  median_elapsed_ms: null,
  p95_elapsed_ms: null,
  input_tokens: 0,
  output_tokens: 0,
  tools: [],
};

describe("AssistantIndicatorsBand", () => {
  it("reads the share of helpful answers and the wait", () => {
    render(
      <AssistantIndicatorsBand
        indicators={{
          ...NOBODY_ASKED,
          kept_since: "2026-10-08T09:30:00Z",
          questions: 5,
          helpful: 3,
          unhelpful: 1,
          unjudged: 1,
          median_elapsed_ms: 5200,
          p95_elapsed_ms: 11000,
          tools: [{ tool: "project_brief", count: 6 }],
        }}
      />,
    );

    expect(screen.getByText("75 %")).toBeInTheDocument();
    expect(screen.getByText("5,2 s")).toBeInTheDocument();
    expect(screen.getByText(/11,0 s pour 95 %/)).toBeInTheDocument();
    expect(screen.getByText("project_brief")).toBeInTheDocument();
    expect(screen.getByText(/depuis le premier, le 8 oct\. 2026/)).toBeInTheDocument();
  });

  it("reads no share of helpful answers while nobody has judged one", () => {
    render(
      <AssistantIndicatorsBand
        indicators={{ ...NOBODY_ASKED, questions: 2, unjudged: 2 }}
      />,
    );

    expect(screen.queryByText("0 %")).not.toBeInTheDocument();
  });

  it("names every cause, even the ones nobody picked", () => {
    render(<AssistantIndicatorsBand indicators={NOBODY_ASKED} />);

    for (const label of [
      "Lecture fausse",
      "Phrase fausse",
      "Hors champ",
      "Bonne réponse",
    ]) {
      expect(screen.getByText(label)).toBeInTheDocument();
    }
  });

  it("says nobody waited rather than an instant answer", () => {
    render(<AssistantIndicatorsBand indicators={NOBODY_ASKED} />);

    expect(screen.getAllByText("—").length).toBeGreaterThan(0);
    expect(screen.queryByText("0,0 s")).not.toBeInTheDocument();
    expect(
      screen.getByText("Aucun échange conservé pour l'instant."),
    ).toBeInTheDocument();
  });
});
