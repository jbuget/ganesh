import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/react";

import { PageHeader } from "./PageHeader";

describe("PageHeader", () => {
  it("announces the page title", () => {
    render(<PageHeader title="Kanban" subtitle="Glissez un projet." />);

    expect(screen.getByRole("heading", { level: 1 })).toHaveTextContent("Kanban");
    expect(screen.getByText("Glissez un projet.")).toBeInTheDocument();
  });

  it("hosts the general actions", () => {
    render(
      <PageHeader
        title="Projets"
        subtitle="Ouvert à toute l'équipe."
        actions={<button>Importer</button>}
      />,
    );

    expect(screen.getByRole("button", { name: "Importer" })).toBeInTheDocument();
  });

  it("does without actions when the page has none", () => {
    const { container } = render(<PageHeader title="Kanban" subtitle="…" />);

    expect(container.querySelectorAll("header > div")).toHaveLength(1);
  });
});
