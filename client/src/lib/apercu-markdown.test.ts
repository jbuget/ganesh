import { describe, expect, it } from "vitest";

import { apercuMarkdown } from "./apercu-markdown";

describe("apercuMarkdown", () => {
  it("laisse un texte simple intact", () => {
    expect(apercuMarkdown("Le cadrage est lancé.")).toBe("Le cadrage est lancé.");
  });

  it("dépouille l'emphase, qui ne se rend pas dans une infobulle", () => {
    expect(apercuMarkdown("La **recette** est _validée_")).toBe(
      "La recette est validée",
    );
  });

  it("garde le libellé d'un lien, pas son adresse", () => {
    expect(apercuMarkdown("Voir [la fiche](https://waat.fr/x)")).toBe("Voir la fiche");
  });

  it("retire les marques de titre et de citation", () => {
    expect(apercuMarkdown("## Point hebdo\n> rien à signaler")).toBe(
      "Point hebdo\nrien à signaler",
    );
  });

  it("marque les puces plutôt que de les effacer", () => {
    expect(apercuMarkdown("- migration\n- recette")).toBe("• migration\n• recette");
  });

  it("laisse intact un identifiant en snake_case", () => {
    expect(apercuMarkdown("Voir latest_by_project() dans le repository")).toBe(
      "Voir latest_by_project() dans le repository",
    );
  });

  it("resserre les lignes vides, qui gonfleraient l'infobulle", () => {
    expect(apercuMarkdown("Premier\n\n\nSecond")).toBe("Premier\nSecond");
  });

  it("tronque un long message sur un mot entier", () => {
    const long = `${"mot ".repeat(100)}fin`;

    const court = apercuMarkdown(long);

    expect(court.length).toBeLessThanOrEqual(241);
    expect(court.endsWith("…")).toBe(true);
    expect(court).not.toContain("mo…");
  });

  it("ne tronque pas ce qui tient déjà", () => {
    expect(apercuMarkdown("Court")).not.toContain("…");
  });
});
