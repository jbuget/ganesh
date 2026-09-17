import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/react";

import { ArchivedCallout } from "./ArchivedCallout";

describe("ArchivedCallout", () => {
  it("dit quand la mission a quitté le référentiel", () => {
    render(<ArchivedCallout archivedAt="2026-09-18T00:36:07.943722" />);

    expect(screen.getByRole("status")).toHaveTextContent(
      "Cette mission a été archivée le 18/09/2026.",
    );
  });

  it("annonce l'archivage même sans date connue", () => {
    render(<ArchivedCallout archivedAt={null} />);

    expect(screen.getByRole("status")).toHaveTextContent("Cette mission est archivée.");
  });
});
