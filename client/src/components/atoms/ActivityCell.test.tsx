import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/react";

import { ActivityCell } from "./ActivityCell";

describe("ActivityCell", () => {
  it("is drawn darker as the level rises", () => {
    render(
      <>
        <ActivityCell level={0} aria-label="calme" role="img" />
        <ActivityCell level={4} aria-label="chargé" role="img" />
      </>,
    );

    expect(screen.getByLabelText("calme")).toHaveClass("bg-slate-100");
    expect(screen.getByLabelText("chargé")).toHaveClass("bg-sky-700");
  });
});
