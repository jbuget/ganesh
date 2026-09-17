import { describe, expect, it, vi } from "vitest";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";

import { ProjectLinksEditor } from "./ProjectLinksEditor";
import type { ProjectLinkResponse } from "@/lib/api/generated/model";

const link = (
  id: number,
  label: string,
  icon: ProjectLinkResponse["icon"] = "link",
): ProjectLinkResponse => ({ id, label, url: `https://waat.fr/${id}`, icon });

function ouvrirLeFormulaire() {
  fireEvent.click(screen.getByRole("button", { name: "Ajouter un lien" }));
}

function saisir(placeholder: string, value: string) {
  fireEvent.change(screen.getByPlaceholderText(placeholder), {
    target: { value: value },
  });
}

describe("ProjectLinksEditor", () => {
  it("n'offre que l'ajout quand la mission n'a aucun lien", () => {
    render(<ProjectLinksEditor links={[]} onAdd={vi.fn()} onRemove={vi.fn()} />);

    expect(screen.queryByRole("link")).not.toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Ajouter un lien" })).toBeInTheDocument();
  });

  it("garde le formulaire ferme tant qu'on ne le demande pas", () => {
    render(<ProjectLinksEditor links={[]} onAdd={vi.fn()} onRemove={vi.fn()} />);

    expect(screen.queryByPlaceholderText("https://…")).not.toBeInTheDocument();
  });

  it("liste tous les liens de la mission", () => {
    render(
      <ProjectLinksEditor
        links={[link(1, "Le dépôt", "repository"), link(2, "Maquettes", "design")]}
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
        links={[link(1, "Le dépôt", "repository")]}
        onAdd={vi.fn()}
        onRemove={vi.fn()}
      />,
    );

    expect(screen.getByLabelText("Dépôt de code")).toBeInTheDocument();
  });

  it("laisse l'adresse décider de l'icône par défaut", async () => {
    const onAdd = vi.fn().mockResolvedValue(undefined);
    render(<ProjectLinksEditor links={[]} onAdd={onAdd} onRemove={vi.fn()} />);

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
    render(<ProjectLinksEditor links={[]} onAdd={onAdd} onRemove={vi.fn()} />);

    ouvrirLeFormulaire();
    fireEvent.click(screen.getByRole("button", { name: "Choisir l'icône du lien" }));
    fireEvent.click(screen.getByRole("button", { name: /Tableur/ }));
    saisir("https://…", "https://waat.fr/budget");
    fireEvent.click(screen.getByRole("button", { name: "Ajouter" }));

    await waitFor(() =>
      expect(onAdd).toHaveBeenCalledWith("", "https://waat.fr/budget", "spreadsheet"),
    );
  });

  it("refuse d'ajouter tant qu'aucune adresse n'est saisie", () => {
    render(<ProjectLinksEditor links={[]} onAdd={vi.fn()} onRemove={vi.fn()} />);

    ouvrirLeFormulaire();

    expect(screen.getByRole("button", { name: "Ajouter" })).toBeDisabled();
  });

  it("explique une adresse refusée par le serveur", async () => {
    const onAdd = vi.fn().mockRejectedValue(new Error("400"));
    render(<ProjectLinksEditor links={[]} onAdd={onAdd} onRemove={vi.fn()} />);

    ouvrirLeFormulaire();
    saisir("https://…", "ftp://waat.fr");
    fireEvent.click(screen.getByRole("button", { name: "Ajouter" }));

    expect(await screen.findByText(/n'est pas valide/)).toBeInTheDocument();
  });

  it("repart d'un formulaire vierge apres un ajout", async () => {
    const onAdd = vi.fn().mockResolvedValue(undefined);
    render(<ProjectLinksEditor links={[]} onAdd={onAdd} onRemove={vi.fn()} />);

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
        links={[link(7, "Maquettes", "design")]}
        onAdd={vi.fn()}
        onRemove={onRemove}
      />,
    );

    fireEvent.click(screen.getByRole("button", { name: "Retirer Maquettes" }));

    expect(onRemove).toHaveBeenCalledWith(7);
  });

  it("offre le retrait de chaque lien sans attendre un survol", () => {
    // La croix ne doit pas se meriter : au doigt, il n'y a pas de survol.
    render(
      <ProjectLinksEditor
        links={[link(1, "Le dépôt", "repository"), link(2, "Maquettes", "design")]}
        onAdd={vi.fn()}
        onRemove={vi.fn()}
      />,
    );

    expect(screen.getByRole("button", { name: "Retirer Le dépôt" })).toBeVisible();
    expect(screen.getByRole("button", { name: "Retirer Maquettes" })).toBeVisible();
  });
});
