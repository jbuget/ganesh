import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/react";

import { PageLayout } from "./PageLayout";

describe("PageLayout", () => {
  it("affiche l'en-tête et le contenu", () => {
    render(
      <PageLayout entete={<h1>Référentiel</h1>}>
        <p>Une mission</p>
      </PageLayout>,
    );

    expect(screen.getByRole("heading", { name: "Référentiel" })).toBeInTheDocument();
    expect(screen.getByText("Une mission")).toBeInTheDocument();
  });

  it("garde l'en-tête hors de la zone qui défile", () => {
    // C'est toute la raison d'etre du squelette : si l'en-tete partageait le
    // conteneur defilant, il s'en irait avec le contenu.
    render(
      <PageLayout entete={<h1>Référentiel</h1>}>
        <p>Une mission</p>
      </PageLayout>,
    );

    const defilante = screen.getByText("Une mission").closest(".overflow-y-auto");

    expect(defilante).not.toBeNull();
    expect(defilante).not.toContainElement(screen.getByRole("heading"));
  });
});
