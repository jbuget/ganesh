import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/react";

import { PageHeader } from "./PageHeader";

describe("PageHeader", () => {
  it("annonce le titre de la page", () => {
    render(<PageHeader titre="Kanban" soustitre="Glissez une mission." />);

    expect(screen.getByRole("heading", { level: 1 })).toHaveTextContent("Kanban");
    expect(screen.getByText("Glissez une mission.")).toBeInTheDocument();
  });

  it("accueille les actions générales", () => {
    render(
      <PageHeader
        titre="Projets"
        soustitre="Ouvert à toute l'équipe."
        actions={<button>Importer</button>}
      />,
    );

    expect(screen.getByRole("button", { name: "Importer" })).toBeInTheDocument();
  });

  it("se passe d'actions quand la page n'en a pas", () => {
    const { container } = render(<PageHeader titre="Kanban" soustitre="…" />);

    expect(container.querySelectorAll("header > div")).toHaveLength(1);
  });
});
