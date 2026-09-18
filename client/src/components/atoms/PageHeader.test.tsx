import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/react";

import { PageHeader } from "./PageHeader";

describe("PageHeader", () => {
  it("announces the page title", () => {
    render(<PageHeader titre="Kanban" soustitre="Glissez une mission." />);

    expect(screen.getByRole("heading", { level: 1 })).toHaveTextContent("Kanban");
    expect(screen.getByText("Glissez une mission.")).toBeInTheDocument();
  });

  it("hosts the general actions", () => {
    render(
      <PageHeader
        titre="Projets"
        soustitre="Ouvert à toute l'équipe."
        actions={<button>Importer</button>}
      />,
    );

    expect(screen.getByRole("button", { name: "Importer" })).toBeInTheDocument();
  });

  it("does without actions when the page has none", () => {
    const { container } = render(<PageHeader titre="Kanban" soustitre="…" />);

    expect(container.querySelectorAll("header > div")).toHaveLength(1);
  });
});
