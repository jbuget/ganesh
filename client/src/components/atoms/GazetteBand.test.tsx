import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/react";

import type { DigestResponse } from "@/lib/api/generated/model";
import { GazetteBand } from "./GazetteBand";

const digest = (over: Partial<DigestResponse>): DigestResponse =>
  ({
    month: "2026-09-01",
    is_generated: false,
    version: null,
    generated_at: null,
    requested_by: null,
    prose: null,
    prose_model: null,
    tally: {},
    chapters: [],
    highlights: [],
    versions: [],
    ...over,
  }) as DigestResponse;

describe("GazetteBand", () => {
  const cursor = { year: 2026, month: 9 };

  it("names the month it is showing", () => {
    render(<GazetteBand cursor={cursor} digest={digest({})} />);

    expect(screen.getByText("septembre 2026")).toBeInTheDocument();
  });

  it("leads to the screen, on the month it was showing", () => {
    render(<GazetteBand cursor={cursor} digest={digest({})} />);

    // A bare address opens on the running month, which is the one the band
    // reads: carrying one would only put a parameter in a link saying nothing.
    expect(screen.getByRole("link", { name: /La Gazette/ })).toHaveAttribute(
      "href",
      "/gazette",
    );
  });

  it("shows the chapeau when a model has written one", () => {
    render(
      <GazetteBand
        cursor={cursor}
        digest={digest({ prose: "Le mois a été calme." })}
      />,
    );

    expect(screen.getByText("Le mois a été calme.")).toBeInTheDocument();
  });

  // Generating is a write: it is traced, and it is kept beside the last
  // version. It belongs on the screen that carries the picker.
  it("offers no way to generate a digest", () => {
    render(<GazetteBand cursor={cursor} digest={digest({})} />);

    expect(screen.queryByRole("button")).toBeNull();
  });
});
