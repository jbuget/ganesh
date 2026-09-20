import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/react";

import { ArchivedCallout } from "./ArchivedCallout";

describe("ArchivedCallout", () => {
  it("says when the mission left the reference list", () => {
    render(<ArchivedCallout archivedAt="2026-09-17T22:36:07.943722Z" />);

    expect(screen.getByRole("status")).toHaveTextContent(
      "Ce projet a été archivé le 18/09/2026.",
    );
  });

  it("announces archiving even with no known date", () => {
    render(<ArchivedCallout archivedAt={null} />);

    expect(screen.getByRole("status")).toHaveTextContent("Ce projet est archivé.");
  });
});
