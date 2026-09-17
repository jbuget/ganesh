import { describe, expect, it, vi } from "vitest";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";

import { ProjectLinksEditor } from "./ProjectLinksEditor";
import type { ProjectLinkResponse } from "@/lib/api/generated/model";

const lien = (
  id: number,
  label: string,
  icone: ProjectLinkResponse["icone"] = "lien",
): ProjectLinkResponse => ({ id, label, url: `https://waat.fr/${id}`, icone });

function ouvrirLeFormulaire() {
  fireEvent.click(screen.getByRole("button", { name: "Ajouter un lien" }));
}

function saisir(placeholder: string, valeur: string) {
  fireEvent.change(screen.getByPlaceholderText(placeholder), {
    target: { value: valeur },
  });
}

describe("ProjectLinksEditor", () => {
  it("annonce une mission sans lien", () => {
    render(<ProjectLinksEditor liens={[]} onAdd={vi.fn()} onRemove={vi.fn()} />);

    expect(screen.getByText("Aucun lien")).toBeInTheDocument();
  });

  it("liste tous les liens de la mission", () => {
    render(
      <ProjectLinksEditor
        liens={[lien(1, "Le dépôt", "depot"), lien(2, "Maquettes", "maquette")]}
        onAdd={vi.fn()}
        onRemove={vi.fn()}
      />,
    );

    expect(screen.getByRole("link", { name: /Le dépôt/ })).toHaveAttribute(
      "href",
      "https://waat.fr/1",
    );
    expect(screen.getByRole("link", { name: /Maquettes/ })).toBeInTheDocument();
  });

  it("annonce l'icône de chaque lien", () => {
    render(
      <ProjectLinksEditor
        liens={[lien(1, "Le dépôt", "depot")]}
        onAdd={vi.fn()}
        onRemove={vi.fn()}
      />,
    );

    expect(screen.getByLabelText("Dépôt de code")).toBeInTheDocument();
  });

  it("laisse l'adresse décider de l'icône par défaut", async () => {
    const onAdd = vi.fn().mockResolvedValue(undefined);
    render(<ProjectLinksEditor liens={[]} onAdd={onAdd} onRemove={vi.fn()} />);

    ouvrirLeFormulaire();
    saisir("Intitulé (facultatif)", "Le dépôt");
    saisir("https://…", "https://github.com/waat/x");
    fireEvent.click(screen.getByRole("button", { name: "Ajouter" }));

    await waitFor(() =>
      expect(onAdd).toHaveBeenCalledWith("Le dépôt", "https://github.com/waat/x", null),
    );
  });

  it("transmet l'icône choisie à la main", async () => {
    const onAdd = vi.fn().mockResolvedValue(undefined);
    render(<ProjectLinksEditor liens={[]} onAdd={onAdd} onRemove={vi.fn()} />);

    ouvrirLeFormulaire();
    fireEvent.click(screen.getByRole("button", { name: "Choisir l'icône du lien" }));
    fireEvent.click(screen.getByRole("button", { name: /Tableur/ }));
    saisir("https://…", "https://waat.fr/budget");
    fireEvent.click(screen.getByRole("button", { name: "Ajouter" }));

    await waitFor(() =>
      expect(onAdd).toHaveBeenCalledWith("", "https://waat.fr/budget", "tableur"),
    );
  });

  it("refuse d'ajouter tant qu'aucune adresse n'est saisie", () => {
    render(<ProjectLinksEditor liens={[]} onAdd={vi.fn()} onRemove={vi.fn()} />);

    ouvrirLeFormulaire();

    expect(screen.getByRole("button", { name: "Ajouter" })).toBeDisabled();
  });

  it("explique une adresse refusée par le serveur", async () => {
    const onAdd = vi.fn().mockRejectedValue(new Error("400"));
    render(<ProjectLinksEditor liens={[]} onAdd={onAdd} onRemove={vi.fn()} />);

    ouvrirLeFormulaire();
    saisir("https://…", "ftp://waat.fr");
    fireEvent.click(screen.getByRole("button", { name: "Ajouter" }));

    expect(await screen.findByText(/n'est pas valide/)).toBeInTheDocument();
  });

  it("repart d'un formulaire vierge apres un ajout", async () => {
    const onAdd = vi.fn().mockResolvedValue(undefined);
    render(<ProjectLinksEditor liens={[]} onAdd={onAdd} onRemove={vi.fn()} />);

    ouvrirLeFormulaire();
    saisir("https://…", "https://waat.fr/x");
    fireEvent.click(screen.getByRole("button", { name: "Ajouter" }));

    await waitFor(() => expect(onAdd).toHaveBeenCalled());
    ouvrirLeFormulaire();
    expect(screen.getByPlaceholderText("https://…")).toHaveValue("");
  });

  it("detache un lien", () => {
    const onRemove = vi.fn().mockResolvedValue(undefined);
    render(
      <ProjectLinksEditor
        liens={[lien(7, "Maquettes", "maquette")]}
        onAdd={vi.fn()}
        onRemove={onRemove}
      />,
    );

    fireEvent.click(screen.getByRole("button", { name: "Retirer Maquettes" }));

    expect(onRemove).toHaveBeenCalledWith(7);
  });
});
