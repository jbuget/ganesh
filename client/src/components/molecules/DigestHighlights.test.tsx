import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it } from "vitest";

import { DigestHighlights } from "./DigestHighlights";
import type { HighlightResponse } from "@/lib/api/generated/model";

function overdue(rank: number): HighlightResponse {
  return {
    kind: "go_live_overdue",
    tone: "attention",
    project_id: rank,
    label: `Projet ${rank}`,
  };
}

const WENT_LIVE: HighlightResponse = {
  kind: "went_live",
  tone: "notable",
  project_id: 99,
  label: "WAATcher",
};

describe("DigestHighlights", () => {
  it("tells what was achieved from what is worth a look", () => {
    render(<DigestHighlights highlights={[WENT_LIVE, overdue(1)]} />);

    expect(screen.getByText(/Faits marquants/)).toBeVisible();
    expect(screen.getByText(/Points d'attention/)).toBeVisible();
  });

  it("leaves out a side the month left empty", () => {
    render(<DigestHighlights highlights={[WENT_LIVE]} />);

    expect(screen.queryByText(/Points d'attention/)).toBeNull();
  });

  it("shows a short list whole", () => {
    render(<DigestHighlights highlights={[1, 2, 3].map(overdue)} />);

    expect(screen.getAllByText(/^Projet \d/)).toHaveLength(3);
    expect(screen.queryByRole("button")).toBeNull();
  });

  it("folds a long list rather than burying what matters", () => {
    /* One tidying-up archives a dozen projects at once, and a dozen identical
       worries bury the one fact of the month that mattered. */
    render(
      <DigestHighlights
        highlights={[WENT_LIVE, ...[1, 2, 3, 4, 5, 6, 7].map(overdue)]}
      />,
    );

    expect(screen.getAllByText(/^Projet \d/)).toHaveLength(5);
    expect(screen.getByRole("button", { name: "Voir les 2 autres" })).toBeVisible();
  });

  it("counts what it folded away, in plain sight", () => {
    render(<DigestHighlights highlights={[1, 2, 3, 4, 5, 6, 7].map(overdue)} />);

    expect(screen.getByText("(7)")).toBeVisible();
  });

  it("unfolds on asking, and folds back", async () => {
    render(<DigestHighlights highlights={[1, 2, 3, 4, 5, 6, 7].map(overdue)} />);

    await userEvent.click(screen.getByRole("button", { name: "Voir les 2 autres" }));
    expect(screen.getAllByText(/^Projet \d/)).toHaveLength(7);

    await userEvent.click(screen.getByRole("button", { name: "Replier" }));
    expect(screen.getAllByText(/^Projet \d/)).toHaveLength(5);
  });
});
